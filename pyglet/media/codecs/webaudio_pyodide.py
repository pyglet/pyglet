from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn, BinaryIO

from pyglet.util import DecodeException

from . import MediaDecoder
from .base import AudioFormat, Source, StaticSource


try:
    import js
    import pyodide.ffi
except ImportError:
    raise ImportError("Pyodide not found.")


from pyglet.media import get_audio_driver

class JavascriptWebAudioSource(Source):
    def __init__(self, filename: str, file: BinaryIO | None=None) -> None:  # noqa: D107
        if file is None:
            with open(filename, 'rb') as f:
                data = f.read()
            self._file = data

        self.filename = filename
        self.js_array = js.Uint8Array.new()
        self.audio_buffer = None
        self._duration = 0
        self._current_offset = 0

        get_audio_driver().decode_audio(self.js_array.buffer).then(self.on_decode).catch(self.on_error)

    # Decode the audio data
    def on_decode(self, audio_buffer) -> None:
        print("Decoded successfully:", audio_buffer)
        self.audio_buffer = audio_buffer

        self.audio_format = AudioFormat(
            channels=self.audio_buffer.numberOfChannels,
            sample_rate=self.audio_buffer.sampleRate,
            sample_size=16,
        )
        self._duration = self.audio_buffer.duration

    def on_error(self, error) -> NoReturn:
        raise DecodeException(error)

    def __del__(self) -> None:
        if hasattr(self, '_file'):
            self._file = None

        self.js_array = None
        self.audio_buffer = None

    def get_audio_data(self, num_bytes: int, compensation_time: float=0.0) -> NoReturn:
        raise NotImplementedError("This is not supported and should not be called.")

    def seek(self, timestamp: float) -> NoReturn:
        raise NotImplementedError("This is not supported and should not be called.")


#########################################
#   Decoder class:
#########################################

class PyodideDecoder(MediaDecoder):  # noqa: D101

    def get_file_extensions(self) -> tuple[str, ...]:
        return '.mp3', '.aac', '.wav', '.ogg', '.webm'
        # possibly use audio.canPlayType?

    def decode(self, filename: str, file: BinaryIO, streaming: bool=True) -> JavascriptWebAudioSource | StaticSource:
        if streaming:
            return JavascriptWebAudioSource(filename, file)
        return StaticSource(JavascriptWebAudioSource(filename, file))


def get_decoders() -> list[PyodideDecoder]:  # noqa: D103
    return [PyodideDecoder()]


def get_encoders() -> list:  # noqa: D103
    return []
