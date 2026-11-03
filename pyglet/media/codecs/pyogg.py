from __future__ import annotations

import pyogg

import os.path
import warnings

from abc import abstractmethod
from _ctypes import CFuncPtr
from typing import TYPE_CHECKING, Any, BinaryIO
from typing import cast as typing_cast
from ctypes import c_void_p, POINTER, c_int, pointer, cast, c_char, c_char_p, CFUNCTYPE, c_ubyte
from ctypes import memmove, create_string_buffer, byref

if TYPE_CHECKING:
    from ctypes import _Pointer, c_size_t, c_uint64

    from pyglet.media.codecs import MediaEncoder

from pyglet import options
from pyglet.media import StreamingSource
from pyglet.media.codecs import AudioFormat, AudioData, MediaDecoder, StaticSource
from pyglet.util import debug_print, DecodeException


_debug = debug_print('Debug PyOgg codec')

if options.debug_media:
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
    pyogg.flac.libflac.FLAC__stream_decoder_init_stream.argtypes = [
        POINTER(pyogg.flac.FLAC__StreamDecoder),
        pyogg.flac.FLAC__StreamDecoderReadCallback,
        c_void_p,  # Seek
        c_void_p,  # Tell
        c_void_p,  # Length
        c_void_p,  # EOF
        pyogg.flac.FLAC__StreamDecoderWriteCallback,
        pyogg.flac.FLAC__StreamDecoderMetadataCallback,
        pyogg.flac.FLAC__StreamDecoderErrorCallback,
        c_void_p
    ]


    def metadata_callback(self: pyogg.FlacFileStream, decoder: _Pointer[pyogg.flac.FLAC__StreamDecoder],
                          metadata: Any, client_data: int | None) -> None:
        self.bits_per_sample = metadata.contents.data.stream_info.bits_per_sample  # missing from pyogg
        self.total_samples = metadata.contents.data.stream_info.total_samples
        self.channels = metadata.contents.data.stream_info.channels
        self.frequency = metadata.contents.data.stream_info.sample_rate


    # Monkey patch metadata callback to include bits per sample as FLAC may rarely deviate from 16 bit.
    pyogg.FlacFileStream.metadata_callback = metadata_callback


class MemoryVorbisObject:
    file: BinaryIO
    read_func: CFuncPtr
    seek_func: CFuncPtr
    close_func: CFuncPtr
    tell_func: CFuncPtr
    callbacks: pyogg.vorbis.ov_callbacks

    def __init__(self, file: BinaryIO) -> None:
        self.file = file

        def read_func_cb(ptr: int, byte_size: int, size_to_read: int, datasource: int | None) -> int:
            data_size = size_to_read * byte_size
            data = self.file.read(data_size)
            read_size = len(data)
            memmove(ptr, data, read_size)
            return read_size

        def seek_func_cb(datasource: int | None, offset: int, whence: int) -> int:
            pos = self.file.seek(offset, whence)
            return pos

        def close_func_cb(datasource: int | None) -> int:
            return 0

        def tell_func_cb(datasource: int | None) -> int:
            return self.file.tell()

        self.read_func = pyogg.vorbis.read_func(read_func_cb)
        self.seek_func = pyogg.vorbis.seek_func(seek_func_cb)
        self.close_func = pyogg.vorbis.close_func(close_func_cb)
        self.tell_func = pyogg.vorbis.tell_func(tell_func_cb)

        self.callbacks = pyogg.vorbis.ov_callbacks(self.read_func, self.seek_func, self.close_func, self.tell_func)


class UnclosedVorbisFileStream(pyogg.VorbisFileStream):
    exists: bool

    def __del__(self) -> None:
        if self.exists:
            pyogg.vorbis.ov_clear(byref(self.vf))
        self.exists = False

    def clean_up(self) -> None:
        """PyOgg calls clean_up on end of data. We may want to loop a sound or replay. Prevent this.
        Rely on GC (__del__) to clean up objects instead.
        """
        return


class UnclosedOpusFileStream(pyogg.OpusFileStream):
    def __del__(self) -> None:
        self.ptr.contents.value = self.ptr_init

        del self.ptr

        if self.of:
            pyogg.opus.op_free(self.of)

    def clean_up(self) -> None:
        pass


class MemoryOpusObject:
    file: BinaryIO
    filename: str
    read_func: CFuncPtr
    seek_func: CFuncPtr
    tell_func: CFuncPtr
    close_func: CFuncPtr
    callbacks: pyogg.opus.OpusFileCallbacks

    def __init__(self, filename: str, file: BinaryIO) -> None:
        self.file = file
        self.filename = filename

        def read_func_cb(stream: int | None, buffer: _Pointer[c_ubyte], size: int) -> int:
            data = self.file.read(size)
            read_size = len(data)
            memmove(buffer, data, read_size)
            return read_size

        def seek_func_cb(stream: int | None, offset: int, whence: int) -> int:
            self.file.seek(offset, whence)
            return 0

        def tell_func_cb(stream: int | None) -> int:
            pos = self.file.tell()
            return pos

        def close_func_cb(stream: int | None) -> int:
            return 0

        self.read_func = pyogg.opus.op_read_func(read_func_cb)
        self.seek_func = pyogg.opus.op_seek_func(seek_func_cb)
        self.tell_func = pyogg.opus.op_tell_func(tell_func_cb)
        self.close_func = pyogg.opus.op_close_func(close_func_cb)

        self.callbacks = pyogg.opus.OpusFileCallbacks(self.read_func, self.seek_func, self.tell_func, self.close_func)


class MemoryOpusFileStream(UnclosedOpusFileStream):
    file: BinaryIO
    memory_object: MemoryOpusObject
    _dummy_fileobj: c_void_p

    def __init__(self, filename: str, file: BinaryIO) -> None:
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
    memory_object: MemoryVorbisObject

    def __init__(self, path: str, file: BinaryIO) -> None:
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
    seekable: bool

    def __init__(self, *args: Any, **kw: Any) -> None:
        super().__init__(*args, **kw)
        self.seekable = True

    def __del__(self) -> None:
        if self.decoder:
            pyogg.flac.FLAC__stream_decoder_finish(self.decoder)


class MemoryFLACFileStream(UnclosedFLACFileStream):
    file: BinaryIO
    file_size: int
    decoder: _Pointer[pyogg.flac.FLAC__StreamDecoder]
    client_data: c_void_p
    write_callback_: CFuncPtr
    metadata_callback_: CFuncPtr
    error_callback_: CFuncPtr
    read_callback_: CFuncPtr
    seek_callback_: CFuncPtr | None
    tell_callback_: CFuncPtr | None
    length_callback_: CFuncPtr | None
    eof_callback_: CFuncPtr | None

    def __init__(self, path: str, file: BinaryIO) -> None:
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
            raise DecodeException("An error occurred when trying to decode the metadata of {}".format(path))

    def read_callback(self, decoder: _Pointer[pyogg.flac.FLAC__StreamDecoder], buffer: _Pointer[c_ubyte],
                      size: _Pointer[c_size_t], data: int | None) -> int:
        chunk = size.contents.value
        chunk_data = self.file.read(chunk)
        read_size = len(chunk_data)
        memmove(buffer, chunk_data, read_size)

        size.contents.value = read_size

        if read_size > 0:
            return 0  # FLAC__STREAM_DECODER_READ_STATUS_CONTINUE
        elif read_size == 0:
            return 1  # FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM
        else:
            return 2  # FLAC__STREAM_DECODER_READ_STATUS_ABORT

    def seek_callback(self, decoder: _Pointer[pyogg.flac.FLAC__StreamDecoder], offset: int, data: int | None) -> int:
        pos = self.file.seek(offset, 0)
        if pos < 0:
            return 1  # FLAC__STREAM_DECODER_SEEK_STATUS_ERROR
        else:
            return 0  # FLAC__STREAM_DECODER_SEEK_STATUS_OK

    def tell_callback(self, decoder: _Pointer[pyogg.flac.FLAC__StreamDecoder], offset: _Pointer[c_uint64],
                      data: int | None) -> int:
        """Decoder wants to know the current position of the file stream."""
        pos = self.file.tell()
        if pos < 0:
            return 1  # FLAC__STREAM_DECODER_TELL_STATUS_ERROR
        else:
            offset.contents.value = pos
            return 0  # FLAC__STREAM_DECODER_TELL_STATUS_OK

    def length_callback(self, decoder: _Pointer[pyogg.flac.FLAC__StreamDecoder], length: _Pointer[c_uint64],
                        data: int | None) -> int:
        """Decoder wants to know the total length of the stream."""
        if self.file_size == 0:
            return 1  # FLAC__STREAM_DECODER_LENGTH_STATUS_ERROR
        else:
            length.contents.value = self.file_size
            return 0  # FLAC__STREAM_DECODER_LENGTH_STATUS_OK

    def eof_callback(self, decoder: _Pointer[pyogg.flac.FLAC__StreamDecoder], data: int | None) -> bool:
        return self.file.tell() >= self.file_size


class PyOggSource(StreamingSource):
    filename: str
    file: BinaryIO | None
    _stream: UnclosedFLACFileStream | UnclosedVorbisFileStream | UnclosedOpusFileStream | None
    sample_size: int

    def __init__(self, filename: str, file: BinaryIO | None) -> None:
        self.filename = filename
        self.file = file
        self._stream = None
        self.sample_size = 16

        self._load_source()
        assert self._stream is not None

        self.audio_format = AudioFormat(channels=self._stream.channels, sample_size=self.sample_size,
                                        sample_rate=self._stream.frequency)

    @abstractmethod
    def _load_source(self) -> None:
        pass

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        """Data returns as c_short_array instead of LP_c_char or c_ubyte, cast each buffer."""
        data = self._stream.get_buffer()  # Returns buffer, length or None
        if data is not None:
            buff, length = data
            buff_char_p = cast(buff, POINTER(c_char))
            # ctypes returns bytes when slicing a character pointer.
            return AudioData(typing_cast(bytes, buff_char_p[:length]), length)

        return None

    def __del__(self) -> None:
        if self._stream:
            del self._stream


class PyOggFLACSource(PyOggSource):
    _duration_per_frame: float

    def _load_source(self) -> None:
        if self.file:
            self._stream = MemoryFLACFileStream(self.filename, self.file)
        else:
            self._stream = UnclosedFLACFileStream(self.filename)

        self.sample_size = self._stream.bits_per_sample
        self._duration = self._stream.total_samples / self._stream.frequency

        # Unknown amount of samples. May occur in some sources.
        if self._stream.total_samples == 0:
            if options.debug_media:
                warnings.warn(f"Unknown amount of samples found in {self.filename}. Seeking may be limited.")
            self._duration_per_frame = 0
        else:
            self._duration_per_frame = self._duration / self._stream.total_samples

    def seek(self, timestamp: float) -> None:
        frame = int(max(0.0, min(timestamp, self._duration)) * self.audio_format.sample_rate)
        self.seek_to_frame(frame)

    def seek_to_frame(self, frame: int) -> None:
        if self._stream.seekable:
            # FLAC exposes an exact decoded sample seek.
            frame = max(0, min(frame, self._stream.total_samples)) if self._stream.total_samples else 0
            seek_succeeded = pyogg.flac.FLAC__stream_decoder_seek_absolute(self._stream.decoder, frame)
            if seek_succeeded is False:
                warnings.warn(f"Failed to seek FLAC file: {self.filename}")
        else:
            warnings.warn(f"Stream is not seekable for FLAC file: {self.filename}.")


class PyOggVorbisSource(PyOggSource):

    def _load_source(self) -> None:
        if self.file:
            self._stream = MemoryVorbisFileStream(self.filename, self.file)
        else:
            self._stream = UnclosedVorbisFileStream(self.filename)

        self._duration = pyogg.vorbis.libvorbisfile.ov_time_total(byref(self._stream.vf), -1)

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        data = self._stream.get_buffer()  # Returns buffer, length or None

        if data is not None:
            return AudioData(*data)

        return None

    def seek(self, timestamp: float) -> None:
        seek_succeeded = pyogg.vorbis.ov_time_seek(self._stream.vf, timestamp)
        if seek_succeeded != 0:
            if options.debug_media:
                warnings.warn(f"Failed to seek file {self.filename} - {seek_succeeded}")


class PyOggOpusSource(PyOggSource):
    _duration_per_frame: float

    def _load_source(self) -> None:
        if self.file:
            self._stream = MemoryOpusFileStream(self.filename, self.file)
        else:
            self._stream = UnclosedOpusFileStream(self.filename)

        self._duration = self._stream.pcm_size / self._stream.frequency
        self._duration_per_frame = self._duration / self._stream.pcm_size

    def seek(self, timestamp: float) -> None:
        frame = int(max(0.0, min(timestamp, self._duration)) * self.audio_format.sample_rate)
        self.seek_to_frame(frame)

    def seek_to_frame(self, frame: int) -> None:
        frame = max(0, min(frame, self._stream.pcm_size))
        error = pyogg.opus.op_pcm_seek(self._stream.of, frame)
        if error:
            warnings.warn(f"Opus stream could not seek properly {error}.")


class PyOggDecoder(MediaDecoder):
    vorbis_exts = ('.ogg',) if pyogg.PYOGG_OGG_AVAIL and pyogg.PYOGG_VORBIS_AVAIL and pyogg.PYOGG_VORBIS_FILE_AVAIL else ()
    flac_exts = ('.flac',) if pyogg.PYOGG_FLAC_AVAIL else ()
    opus_exts = ('.opus',) if pyogg.PYOGG_OPUS_AVAIL and pyogg.PYOGG_OPUS_FILE_AVAIL else ()
    exts = vorbis_exts + flac_exts + opus_exts

    def get_file_extensions(self) -> tuple[str, ...]:
        return PyOggDecoder.exts

    def decode(self, filename: str, file: BinaryIO | None, streaming: bool = True,
               *args: object, **kwargs: object) -> PyOggSource | StaticSource:
        name, ext = os.path.splitext(filename)
        source: type[PyOggSource]
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


def get_decoders() -> list[PyOggDecoder]:
    return [PyOggDecoder()]


def get_encoders() -> list[MediaEncoder]:
    return []
