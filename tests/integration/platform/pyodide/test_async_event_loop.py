from __future__ import annotations

import sys

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from pyglet import app
from pyglet.app.async_app import AsyncEventLoop, AsyncPlatformEventLoop, RequestAnimationFrameDrawSource
from pyglet.event import EventDispatcher


class _EventTarget(EventDispatcher):
    def __init__(self) -> None:
        self.received: list[int] = []

    def on_value(self, value: int) -> None:
        self.received.append(value)


_EventTarget.register_event_type("on_value")


def test_window_close_exits_synchronously(monkeypatch):
    loop = AsyncEventLoop()
    assert not loop._has_exit_event.is_set()  # noqa: SLF001
    monkeypatch.setattr(app, "windows", set())

    loop.dispatch_event("on_window_close", None)

    assert loop._has_exit_event.is_set()  # noqa: SLF001


def test_post_event_matches_platform_event_loop_contract(monkeypatch):
    loop = AsyncPlatformEventLoop()
    target = _EventTarget()

    monkeypatch.setattr(app, "platform_event_loop", loop)
    loop.start()
    target.post_event("on_value", 42)
    loop.dispatch_posted_events()
    loop.stop()

    assert target.received == [42]


def test_request_animation_frame_draw_source_uses_browser_timestamps(monkeypatch):
    loop = AsyncEventLoop()
    draws: list[float] = []
    monkeypatch.setattr(loop, "_redraw_windows", draws.append)
    source = RequestAnimationFrameDrawSource(loop)
    monkeypatch.setattr(source, "_request_next_frame", lambda: None)

    source.start(1 / 60)
    source._on_animation_frame(1000)  # noqa: SLF001
    source._on_animation_frame(1016)  # noqa: SLF001
    source.stop()

    assert draws == pytest.approx([0.0, 0.016])
