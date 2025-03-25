from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from pyglet.util import DecodeException
from .base import StreamingSource, AudioData, AudioFormat, StaticSource, StaticMemorySource, Source
from . import MediaDecoder

if TYPE_CHECKING:
    from pyglet.media.drivers.pyodide_js.adaptation import JSAudioDriver

try:
    import pyodide.ffi
    import js
except ImportError:
    raise ImportError("Pyodide not found.")

class PyodideJSDecodeException(DecodeException):
    pass

from pyglet.media import get_audio_driver

_audio_driver: JSAudioDriver = get_audio_driver()

class PyodideJS_Source(Source):
    def __init__(self, filename: str, file=None):
        if file is None:
            file = open(filename, 'rb')
            self._file = file

        self.filename = filename
        self.js_array = js.Uint8Array.new(self._file.read())
        self.audio_buffer = None
        self._duration = 0
        self._current_offset = 0

        _audio_driver.decode_audio(self.js_array.buffer).then(self.on_decode).catch(self.on_error)

    # Decode the audio data
    def on_decode(self, audio_buffer):
        print("Decoded successfully:", audio_buffer)
        self.audio_buffer = audio_buffer

        self.audio_format = AudioFormat(
            channels=self.audio_buffer.numberOfChannels,
            sample_rate=self.audio_buffer.sampleRate,
            sample_size=16
        )
        self._duration = self.audio_buffer.duration

    def on_error(self, error):
        raise DecodeException(error)

    def __del__(self):
        if hasattr(self, '_file'):
            self._file.close()
            self._file = None

        self.js_array = None
        self.audio_buffer = None

    def get_audio_data(self, num_bytes, compensation_time=0.0):
        raise NotImplementedError("This is not supported and should not be called.")

    def seek(self, timestamp):
        raise NotImplementedError("This is not supported and should not be called.")


#########################################
#   Decoder class:
#########################################

class PyodideDecoder(MediaDecoder):

    def get_file_extensions(self):
        return '.mp3', '.aac', '.wav', '.ogg', '.webm'
        # possibly use audio.canPlayType?

    def decode(self, filename, file, streaming=True):
        if streaming:
            return PyodideJS_Source(filename, file)
        else:
            return StaticSource(PyodideJS_Source(filename, file))


def get_decoders():
    return [PyodideDecoder()]


def get_encoders():
    return []
