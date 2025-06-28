from __future__ import annotations

import weakref
from typing import BinaryIO, NoReturn, TYPE_CHECKING

import pyglet

from . import MediaDecoder
from .base import AudioFormat, Source, StaticSource

_debug = pyglet.options.debug_media

try:
    import js
    import pyodide.ffi
except ImportError:
    raise ImportError("Pyodide not found.")


from pyglet.media import get_audio_driver

if TYPE_CHECKING:
    from pyglet.media.drivers.pyodide_js.adaptation import PyodideJSAudioPlayer


class JavascriptWebAudioSource(Source):
    def __init__(self, filename: str, file: BinaryIO | None = None) -> None:  # noqa: D107
        if file is None:
            with open(filename, 'rb') as f:
                data = f.read()
            self._file = data
        else:
            self._file = file.read()

        self.filename = filename
        self.js_array = js.Uint8Array.new(self._file)
        self.audio_buffer = None
        self._duration = 0
        self._current_offset = 0

        # Default dummy audio format so AudioPlayer can create an internal PyodideJSAudioPlayer.
        # The JavaScript internal player doesn't use this object.
        self.audio_format = AudioFormat(channels=2, sample_size=16, sample_rate=44100)

        # If this audio is not finished loading, a player may be waiting to play it.
        self._waiting_players = weakref.WeakSet()

        get_audio_driver().decode_audio(self.js_array.buffer).then(self.on_decode).catch(self.on_error)

    def add_player(self, player: PyodideJSAudioPlayer) -> None:
        self._waiting_players.add(player)

    # Decode the audio data
    def on_decode(self, audio_buffer) -> None:
        if _debug:
            print(f"Decoded {self.filename} successfully.")
        self.audio_buffer = audio_buffer

        self.audio_format = AudioFormat(
            channels=self.audio_buffer.numberOfChannels,
            sample_size=16,
            sample_rate=self.audio_buffer.sampleRate,
        )
        self._duration = self.audio_buffer.duration

        for player in self._waiting_players:
            player.on_source_finished_loading(self)

        self._waiting_players.clear()

    def on_error(self, error) -> NoReturn:
        js.console.log(f"Failed decoding {self.filename}: {error}")

        self._waiting_players.clear()

    def __del__(self) -> None:
        if hasattr(self, '_file'):
            self._file = None

        self.js_array = None
        self.audio_buffer = None

    def get_audio_data(self, num_bytes: int, compensation_time: float = 0.0) -> NoReturn:
        raise NotImplementedError("This is not supported and should not be called.")

    def seek(self, timestamp: float) -> NoReturn:
        """This is not supported by Javascript."""


#########################################
#   Decoder class:
#########################################


class PyodideDecoder(MediaDecoder):  # noqa: D101
    def get_file_extensions(self) -> tuple[str, ...]:
        return '.mp3', '.aac', '.wav', '.ogg', '.webm'
        # possibly use audio.canPlayType?

    def decode(self, filename: str, file: BinaryIO, streaming: bool = True) -> JavascriptWebAudioSource | StaticSource:
        if streaming:
            return JavascriptWebAudioSource(filename, file)
        return StaticSource(JavascriptWebAudioSource(filename, file))


def get_decoders() -> list[PyodideDecoder]:  # noqa: D103
    return [PyodideDecoder()]


def get_encoders() -> list:  # noqa: D103
    return []
