from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from pyglet import app
from pyglet.app.async_app import AsyncPlatformEventLoop
from pyglet.event import EventDispatcher
from pyglet.media.codecs.base import AudioFormat, Source
from pyglet.media.drivers.pyodide_js.adaptation import PyodideJSAudioPlayer


class _EOSPlayer(EventDispatcher):
    def __init__(self):
        self.received = 0

    def on_eos(self):
        self.received += 1


_EOSPlayer.register_event_type("on_eos")


def test_audio_end_posts_eos(monkeypatch):
    loop = AsyncPlatformEventLoop()
    monkeypatch.setattr(app, "platform_event_loop", loop)
    source = Source()
    source.audio_format = AudioFormat(1, 16, 44100)
    source.audio_buffer = object()
    player = _EOSPlayer()
    audio_player = PyodideJSAudioPlayer(MagicMock(), source, player)
    audio_player._playing = True

    loop.start()
    try:
        audio_player._source_player.onended(None)

        assert not audio_player._playing
        assert player.received == 0
        loop.dispatch_posted_events()
        assert player.received == 1
    finally:
        audio_player.delete()
        loop.stop()
