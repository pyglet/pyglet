import os.path
import pyogg
import pyglet
from ctypes import c_void_p, POINTER, memmove, create_string_buffer, byref, c_int, pointer, cast, c_char, c_char_p, \
    CFUNCTYPE

from pyglet.media import StreamingSource
from pyglet.media.codecs import AudioFormat, AudioData, MediaDecoder, StaticSource
import warnings

def metadata_callback(self, decoder, metadata, client_data):
    self.bits_per_sample = metadata.contents.data.stream_info.bits_per_sample  # missing from pyogg
    self.total_samples = metadata.contents.data.stream_info.total_samples
    self.channels = metadata.contents.data.stream_info.channels
    self.frequency = metadata.contents.data.stream_info.sample_rate


# Monkey patch our own function for callback to get the bits per sample.
pyogg.FlacFileStream.metadata_callback = metadata_callback


class MemoryVorbisObject:
    def __init__(self, file):
        self.file = file

        def read_func_cb(ptr, byte_size, size_to_read, datasource):
            data_size = size_to_read * byte_size
            data = self.file.read(data_size)
            read_size = len(data)
            memmove(ptr, data, read_size)
            return read_size

        def seek_func_cb(datasource, offset, whence):
            pos = self.file.seek(offset, whence)
            return pos

        def close_func_cb(datasource):
            return 0

        def tell_func_cb(datasource):
            return self.file.tell()

        self.read_func = pyogg.vorbis.read_func(read_func_cb)
        self.seek_func = pyogg.vorbis.seek_func(seek_func_cb)
        self.close_func = pyogg.vorbis.close_func(close_func_cb)
        self.tell_func = pyogg.vorbis.tell_func(tell_func_cb)

        self.callbacks = pyogg.vorbis.ov_callbacks(self.read_func, self.seek_func, self.close_func, self.tell_func)


class UnclosedVorbisFileStream(pyogg.VorbisFileStream):
    def __del__(self):
        if self.exists:
            vorbis.ov_clear(ctypes.byref(self.vf))
        self.exists = False

    def clean_up(self):
        """PyOgg calls clean_up on end of data. We may want to loop a sound or replay.
        Rely on GC to clean up instead.
        """
        return

class MemoryVorbisFileStream(UnclosedVorbisFileStream):
    def __init__(self, path, file):
        buff = create_string_buffer(pyogg.PYOGG_STREAM_BUFFER_SIZE)

        self.vf = pyogg.vorbis.OggVorbis_File()
        self.memory_object = MemoryVorbisObject(file)

        error = pyogg.vorbis.libvorbisfile.ov_open_callbacks(buff, self.vf, None, 0, self.memory_object.callbacks)
        if error != 0:
            raise PyOggError("file couldn't be opened or doesn't exist. Error code : {}".format(error))

        info = pyogg.vorbis.ov_info(byref(self.vf), -1)

        self.channels = info.contents.channels

        self.frequency = info.contents.rate

        array = (c_char * (pyogg.PYOGG_STREAM_BUFFER_SIZE * self.channels))()

        self.buffer_ = cast(pointer(array), c_char_p)

        self.bitstream = c_int()
        self.bitstream_pointer = pointer(self.bitstream)

        self.exists = True


# Some monkey patching PyOgg.
# Original in PyOgg: FLAC__StreamDecoderEofCallback = CFUNCTYPE(FLAC__bool, POINTER(FLAC__StreamDecoder), c_void_p)
# FLAC__bool is not valid for this return type (at least for ctypes). Needs to be an int.
FLAC__StreamDecoderEofCallback = CFUNCTYPE(c_int, POINTER(pyogg.flac.FLAC__StreamDecoder), c_void_p)

# Override explicits with void_p, so we can support non-seeking files as well.
if pyogg.PYOGG_FLAC_AVAIL:
    pyogg.flac.libflac.FLAC__stream_decoder_init_stream.restype = pyogg.flac.FLAC__StreamDecoderInitStatus
    pyogg.flac.libflac.FLAC__stream_decoder_init_stream.argtypes = [POINTER(pyogg.flac.FLAC__StreamDecoder),
                                                                    pyogg.flac.FLAC__StreamDecoderReadCallback,
                                                                    c_void_p,  # Seek
                                                                    c_void_p,  # Tell
                                                                    c_void_p,  # Length
                                                                    c_void_p,  # EOF
                                                                    pyogg.flac.FLAC__StreamDecoderWriteCallback,
                                                                    pyogg.flac.FLAC__StreamDecoderMetadataCallback,
                                                                    pyogg.flac.FLAC__StreamDecoderErrorCallback,
                                                                    c_void_p]

class UnclosedFLACFileStream(pyogg.FlacFileStream):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.seekable = True


class MemoryFLACFileStream(UnclosedFLACFileStream):
    def __init__(self, path, file):
        self.file = file

        self.file_size = 0

        if getattr(self.file, 'seek', None) and getattr(self.file, 'tell', None):
            self.seekable = True
            self.file.seek(0, 2)
            self.file_size = self.file.tell()
            self.file.seek(0)
        else:
            warnings.warn(f"Warning: {file} file object is not seekable.")
            self.seekable = False

        self.decoder = pyogg.flac.FLAC__stream_decoder_new()

        self.client_data = c_void_p()

        self.channels = None

        self.frequency = None

        self.total_samples = None

        self.buffer = None

        self.bytes_written = None

        self.write_callback_ = pyogg.flac.FLAC__StreamDecoderWriteCallback(self.write_callback)
        self.metadata_callback_ = pyogg.flac.FLAC__StreamDecoderMetadataCallback(self.metadata_callback)
        self.error_callback_ = pyogg.flac.FLAC__StreamDecoderErrorCallback(self.error_callback)
        self.read_callback_ = pyogg.flac.FLAC__StreamDecoderReadCallback(self.read_callback)

        if self.seekable:
            self.seek_callback_ = pyogg.flac.FLAC__StreamDecoderSeekCallback(self.seek_callback)
            self.tell_callback_ = pyogg.flac.FLAC__StreamDecoderTellCallback(self.tell_callback)
            self.length_callback_ = pyogg.flac.FLAC__StreamDecoderLengthCallback(self.length_callback)
            self.eof_callback_ = FLAC__StreamDecoderEofCallback(self.eof_callback)
        else:
            self.seek_callback_ = None
            self.tell_callback_ = None
            self.length_callback_ = None
            self.eof_callback_ = None

        init_status = pyogg.flac.libflac.FLAC__stream_decoder_init_stream(
            self.decoder,
            self.read_callback_,
            self.seek_callback_,
            self.tell_callback_,
            self.length_callback_,
            self.eof_callback_,
            self.write_callback_,
            self.metadata_callback_,
            self.error_callback_,
            self.client_data
        )

        if init_status:  # error
            raise pyogg.PyOggError("An error occurred when trying to open '{}': {}".format(path,
                                                                                           pyogg.flac.FLAC__StreamDecoderInitStatusEnum[
                                                                                               init_status]))

        metadata_status = pyogg.flac.FLAC__stream_decoder_process_until_end_of_metadata(self.decoder)
        if not metadata_status:  # error
            raise pyogg.PyOggError("An error occured when trying to decode the metadata of {}".format(path))

    def read_callback(self, decoder, buffer, size, data):
        chunk = size.contents.value
        data = self.file.read(chunk)
        read_size = len(data)
        memmove(buffer, data, read_size)

        size.contents.value = read_size

        if read_size > 0:
            return 0  # FLAC__STREAM_DECODER_READ_STATUS_CONTINUE
        elif read_size == 0:
            return 1  # FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM
        else:
            return 2  # FLAC__STREAM_DECODER_READ_STATUS_ABORT

    def seek_callback(self, decoder, offset, data):
        pos = self.file.seek(offset, 0)
        if pos < 0:
            return 1  # FLAC__STREAM_DECODER_SEEK_STATUS_ERROR
        else:
            return 0  # FLAC__STREAM_DECODER_SEEK_STATUS_OK

    def tell_callback(self, decoder, offset, data):
        """Decoder wants to know the current position of the file stream."""
        pos = self.file.tell()
        if pos < 0:
            return 1  # FLAC__STREAM_DECODER_TELL_STATUS_ERROR
        else:
            offset.contents.value = pos
            return 0  # FLAC__STREAM_DECODER_TELL_STATUS_OK

    def length_callback(self, decoder, length, data):
        """Decoder wants to know the total length of the stream."""
        if self.file_size == 0:
            return 1  # FLAC__STREAM_DECODER_LENGTH_STATUS_ERROR
        else:
            length.contents.value = self.file_size
            return 0  # FLAC__STREAM_DECODER_LENGTH_STATUS_OK

    def eof_callback(self, decoder, data):
        return self.file.tell() >= self.file_size


class PyOggSource(StreamingSource):

    def __init__(self, filename, file=None):
        self.filename = filename
        self._vorbis = False
        self._flac = False

        name, ext = os.path.splitext(filename)

        if ext == '.ogg':
            if not pyogg.PYOGG_VORBIS_AVAIL:
                raise Exception("PyOgg determined that VORBIS is unavailable.")
            self._vorbis = True
            if file:
                self._stream = MemoryVorbisFileStream(filename, file)
            else:
                self._stream = UnclosedVorbisFileStream(filename)
            sample_size = 16
            self._duration = pyogg.vorbis.libvorbisfile.ov_time_total(byref(self._stream.vf), -1)
        elif ext == '.flac':
            if not pyogg.PYOGG_FLAC_AVAIL:
                raise Exception("PyOgg determined that FLAC is unavailable.")

            self._flac = True
            if file:
                self._stream = MemoryFLACFileStream(filename, file)
            else:
                self._stream = UnclosedFLACFileStream(filename)

            sample_size = self._stream.bits_per_sample
            self.get_audio_data = self._get_flac_audio_data  # Assign proper function.

            self._duration = self._stream.total_samples / self._stream.frequency

            # Unknown amount of samples. May occur in some sources.
            if self._stream.total_samples == 0:
                warnings.warn(f"Unknown amount of samples found in {filename}. Seeking may be limited.")
                self._duration_per_frame = 0
            else:
                self._duration_per_frame = self._duration / self._stream.total_samples

        else:
            raise Exception(f"No supported file extension could be found for {filename}.")

        self.audio_format = AudioFormat(channels=self._stream.channels, sample_size=sample_size,
                                        sample_rate=self._stream.frequency)

    def __del__(self):
        try:
            self._stream.clean_up()
        except:
            pass

    def _get_flac_audio_data(self, num_bytes, compensation_time=0.0):
        """Flac decoder returns as c_short_array instead of LP_c_char or c_ubyte, cast each buffer."""
        data = self._stream.get_buffer()  # Returns buffer, length or None
        if data is not None:
            buff, length = data
            buff_char_p = cast(buff, POINTER(c_char))
            return AudioData(buff_char_p[:length], length, 1000, 1000, [])

        return None

    def get_audio_data(self, num_bytes, compensation_time=0.0):
        data = self._stream.get_buffer()  # Returns buffer, length or None

        if data is not None:
            return AudioData(*data, 1000, 1000, [])

        return None

    def seek(self, timestamp):
        if self._vorbis:
            seek_succeeded = pyogg.vorbis.ov_time_seek(self._stream.vf, timestamp)
            if seek_succeeded != 0:
                warnings.warn(f"Failed to seek file {filename} - {seek_succeeded}")

        elif self._flac:
            if self._stream.seekable:
                # Convert sample to seconds.
                if self._duration_per_frame:
                    timestamp = max(0.0, min(timestamp, self._duration))
                    position = int(timestamp / self._duration_per_frame)
                else:  # If we have no duration, we cannot seek. However, 0.0 is still required for loops.
                    position = 0
                seek_succeeded = pyogg.flac.FLAC__stream_decoder_seek_absolute(self._stream.decoder, position)
                if seek_succeeded is False:
                    warnings.warn(f"Failed to seek FLAC file: {self.filename}")
            else:
                warnings.warn(f"Stream is not seekable for FLAC file: {self.filename}.")


class PyOggDecoder(MediaDecoder):
    def get_file_extensions(self):
        return '.ogg', '.flac'

    def decode(self, file, filename, streaming=True):
        if streaming:
            return PyOggSource(filename, file)
        else:
            return StaticSource(PyOggSource(filename, file))

