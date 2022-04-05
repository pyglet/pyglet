import pyogg

import os.path
import warnings

from abc import abstractmethod
from ctypes import c_void_p, POINTER, c_int, pointer, cast, c_char, c_char_p, CFUNCTYPE, c_ubyte
from ctypes import memmove, create_string_buffer, byref

from pyglet.media import StreamingSource
from pyglet.media.codecs import AudioFormat, AudioData, MediaDecoder, StaticSource
from pyglet.util import debug_print, DecodeException


_debug = debug_print('Debug PyOgg codec')

if _debug:
    if not pyogg.PYOGG_OGG_AVAIL and not pyogg.PYOGG_VORBIS_AVAIL and not pyogg.PYOGG_VORBIS_FILE_AVAIL:
        warnings.warn("PyOgg determined the ogg/vorbis libraries were not available.")

    if not pyogg.PYOGG_FLAC_AVAIL:
        warnings.warn("PyOgg determined the flac library was not available.")

    if not pyogg.PYOGG_OPUS_AVAIL and not pyogg.PYOGG_OPUS_FILE_AVAIL:
        warnings.warn("PyOgg determined the opus libraries were not available.")

if not (
        pyogg.PYOGG_OGG_AVAIL and not pyogg.PYOGG_VORBIS_AVAIL and not pyogg.PYOGG_VORBIS_FILE_AVAIL) and (
        not pyogg.PYOGG_OPUS_AVAIL and not pyogg.PYOGG_OPUS_FILE_AVAIL) and not pyogg.PYOGG_FLAC_AVAIL:
    raise ImportError("PyOgg determined no supported libraries were found")

# Some monkey patching PyOgg for FLAC.
if pyogg.PYOGG_FLAC_AVAIL:
    # Original in PyOgg: FLAC__StreamDecoderEofCallback = CFUNCTYPE(FLAC__bool, POINTER(FLAC__StreamDecoder), c_void_p)
    # FLAC__bool is not valid for this return type (at least for ctypes). Needs to be an int or an error occurs.
    FLAC__StreamDecoderEofCallback = CFUNCTYPE(c_int, POINTER(pyogg.flac.FLAC__StreamDecoder), c_void_p)

    # Override explicits with c_void_p, so we can support non-seeking FLAC's (CFUNCTYPE does not accept None).
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


    def metadata_callback(self, decoder, metadata, client_data):
        self.bits_per_sample = metadata.contents.data.stream_info.bits_per_sample  # missing from pyogg
        self.total_samples = metadata.contents.data.stream_info.total_samples
        self.channels = metadata.contents.data.stream_info.channels
        self.frequency = metadata.contents.data.stream_info.sample_rate


    # Monkey patch metadata callback to include bits per sample as FLAC may rarely deviate from 16 bit.
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
            pyogg.vorbis.ov_clear(byref(self.vf))
        self.exists = False

    def clean_up(self):
        """PyOgg calls clean_up on end of data. We may want to loop a sound or replay. Prevent this.
        Rely on GC (__del__) to clean up objects instead.
        """
        return


class UnclosedOpusFileStream(pyogg.OpusFileStream):
    def __del__(self):
        self.ptr.contents.value = self.ptr_init

        del self.ptr

        if self.of:
            pyogg.opus.op_free(self.of)

    def clean_up(self):
        pass


class MemoryOpusObject:
    def __init__(self, filename, file):
        self.file = file
        self.filename = filename

        def read_func_cb(stream, buffer, size):
            data = self.file.read(size)
            read_size = len(data)
            memmove(buffer, data, read_size)
            return read_size

        def seek_func_cb(stream, offset, whence):
            self.file.seek(offset, whence)
            return 0

        def tell_func_cb(stream):
            pos = self.file.tell()
            return pos

        def close_func_cb(stream):
            return 0

        self.read_func = pyogg.opus.op_read_func(read_func_cb)
        self.seek_func = pyogg.opus.op_seek_func(seek_func_cb)
        self.tell_func = pyogg.opus.op_tell_func(tell_func_cb)
        self.close_func = pyogg.opus.op_close_func(close_func_cb)

        self.callbacks = pyogg.opus.OpusFileCallbacks(self.read_func, self.seek_func, self.tell_func, self.close_func)


class MemoryOpusFileStream(UnclosedOpusFileStream):
    def __init__(self, filename, file):
        self.file = file

        self.memory_object = MemoryOpusObject(filename, file)

        self._dummy_fileobj = c_void_p()

        error = c_int()

        self.read_buffer = create_string_buffer(pyogg.PYOGG_STREAM_BUFFER_SIZE)

        self.ptr_buffer = cast(self.read_buffer, POINTER(c_ubyte))

        self.of = pyogg.opus.op_open_callbacks(
            self._dummy_fileobj,
            byref(self.memory_object.callbacks),
            self.ptr_buffer,
            0,  # Start length
            byref(error)
        )

        if error.value != 0:
            raise DecodeException(
                "file-like object: {} couldn't be processed. Error code : {}".format(filename, error.value))

        self.channels = pyogg.opus.op_channel_count(self.of, -1)

        self.pcm_size = pyogg.opus.op_pcm_total(self.of, -1)

        self.frequency = 48000

        self.bfarr_t = pyogg.opus.opus_int16 * (pyogg.PYOGG_STREAM_BUFFER_SIZE * self.channels * 2)

        self.buffer = cast(pointer(self.bfarr_t()), pyogg.opus.opus_int16_p)

        self.ptr = cast(pointer(self.buffer), POINTER(c_void_p))

        self.ptr_init = self.ptr.contents.value


class MemoryVorbisFileStream(UnclosedVorbisFileStream):
    def __init__(self, path, file):
        buff = create_string_buffer(pyogg.PYOGG_STREAM_BUFFER_SIZE)

        self.vf = pyogg.vorbis.OggVorbis_File()
        self.memory_object = MemoryVorbisObject(file)

        error = pyogg.vorbis.libvorbisfile.ov_open_callbacks(buff, self.vf, None, 0, self.memory_object.callbacks)
        if error != 0:
            raise DecodeException("file couldn't be opened or doesn't exist. Error code : {}".format(error))

        info = pyogg.vorbis.ov_info(byref(self.vf), -1)

        self.channels = info.contents.channels

        self.frequency = info.contents.rate

        array = (c_char * (pyogg.PYOGG_STREAM_BUFFER_SIZE * self.channels))()

        self.buffer_ = cast(pointer(array), c_char_p)

        self.bitstream = c_int()
        self.bitstream_pointer = pointer(self.bitstream)

        self.exists = True


class UnclosedFLACFileStream(pyogg.FlacFileStream):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.seekable = True

    def __del__(self):
        if self.decoder:
            pyogg.flac.FLAC__stream_decoder_finish(self.decoder)


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
            raise DecodeException("An error occurred when trying to open '{}': {}".format(
                path, pyogg.flac.FLAC__StreamDecoderInitStatusEnum[init_status]))

        metadata_status = pyogg.flac.FLAC__stream_decoder_process_until_end_of_metadata(self.decoder)
        if not metadata_status:  # error
            raise DecodeException("An error occured when trying to decode the metadata of {}".format(path))

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
    def __init__(self, filename, file):
        self.filename = filename
        self.file = file
        self._stream = None
        self.sample_size = 16

        self._load_source()

        self.audio_format = AudioFormat(channels=self._stream.channels, sample_size=self.sample_size,
                                        sample_rate=self._stream.frequency)

    @abstractmethod
    def _load_source(self):
        pass

    def get_audio_data(self, num_bytes, compensation_time=0.0):
        """Data returns as c_short_array instead of LP_c_char or c_ubyte, cast each buffer."""
        data = self._stream.get_buffer()  # Returns buffer, length or None
        if data is not None:
            buff, length = data
            buff_char_p = cast(buff, POINTER(c_char))
            return AudioData(buff_char_p[:length], length, 1000, 1000, [])

        return None

    def __del__(self):
        if self._stream:
            del self._stream


class PyOggFLACSource(PyOggSource):

    def _load_source(self):
        if self.file:
            self._stream = MemoryFLACFileStream(self.filename, self.file)
        else:
            self._stream = UnclosedFLACFileStream(self.filename)

        self.sample_size = self._stream.bits_per_sample
        self._duration = self._stream.total_samples / self._stream.frequency

        # Unknown amount of samples. May occur in some sources.
        if self._stream.total_samples == 0:
            if _debug:
                warnings.warn(f"Unknown amount of samples found in {self.filename}. Seeking may be limited.")
            self._duration_per_frame = 0
        else:
            self._duration_per_frame = self._duration / self._stream.total_samples

    def seek(self, timestamp):
        if self._stream.seekable:
            # Convert sample to seconds.
            if self._duration_per_frame:
                timestamp = max(0.0, min(timestamp, self._duration))
                position = int(timestamp / self._duration_per_frame)
            else:  # If we have no duration, we cannot reliably seek. However, 0.0 is still required to play and loop.
                position = 0
            seek_succeeded = pyogg.flac.FLAC__stream_decoder_seek_absolute(self._stream.decoder, position)
            if seek_succeeded is False:
                warnings.warn(f"Failed to seek FLAC file: {self.filename}")
        else:
            warnings.warn(f"Stream is not seekable for FLAC file: {self.filename}.")


class PyOggVorbisSource(PyOggSource):

    def _load_source(self):
        if self.file:
            self._stream = MemoryVorbisFileStream(self.filename, self.file)
        else:
            self._stream = UnclosedVorbisFileStream(self.filename)

        self._duration = pyogg.vorbis.libvorbisfile.ov_time_total(byref(self._stream.vf), -1)

    def get_audio_data(self, num_bytes, compensation_time=0.0):
        data = self._stream.get_buffer()  # Returns buffer, length or None

        if data is not None:
            return AudioData(*data, 1000, 1000, [])

        return None

    def seek(self, timestamp):
        seek_succeeded = pyogg.vorbis.ov_time_seek(self._stream.vf, timestamp)
        if seek_succeeded != 0:
            if _debug:
                warnings.warn(f"Failed to seek file {self.filename} - {seek_succeeded}")


class PyOggOpusSource(PyOggSource):
    def _load_source(self):
        if self.file:
            self._stream = MemoryOpusFileStream(self.filename, self.file)
        else:
            self._stream = UnclosedOpusFileStream(self.filename)

        self._duration = self._stream.pcm_size / self._stream.frequency
        self._duration_per_frame = self._duration / self._stream.pcm_size

    def seek(self, timestamp):
        timestamp = max(0.0, min(timestamp, self._duration))
        position = int(timestamp / self._duration_per_frame)
        error = pyogg.opus.op_pcm_seek(self._stream.of, position)
        if error:
            warnings.warn(f"Opus stream could not seek properly {error}.")


class PyOggDecoder(MediaDecoder):
    vorbis_exts = ('.ogg',) if pyogg.PYOGG_OGG_AVAIL and pyogg.PYOGG_VORBIS_AVAIL and pyogg.PYOGG_VORBIS_FILE_AVAIL else ()
    flac_exts = ('.flac',) if pyogg.PYOGG_FLAC_AVAIL else ()
    opus_exts = ('.opus',) if pyogg.PYOGG_OPUS_AVAIL and pyogg.PYOGG_OPUS_FILE_AVAIL else ()
    exts = vorbis_exts + flac_exts + opus_exts

    def get_file_extensions(self):
        return PyOggDecoder.exts

    def decode(self, filename, file, streaming=True):
        name, ext = os.path.splitext(filename)
        if ext in PyOggDecoder.vorbis_exts:
            source = PyOggVorbisSource
        elif ext in PyOggDecoder.flac_exts:
            source = PyOggFLACSource
        elif ext in PyOggDecoder.opus_exts:
            source = PyOggOpusSource
        else:
            raise DecodeException("Decoder could not find a suitable source to use with this filetype.")

        if streaming:
            return source(filename, file)
        else:
            return StaticSource(source(filename, file))


def get_decoders():
    return [PyOggDecoder()]


def get_encoders():
    return []
