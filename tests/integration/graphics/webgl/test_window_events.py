from __future__ import annotations

from js import KeyboardEvent, Object
from pyodide.ffi import to_js

import pyglet


def test_browser_event_wakes_the_event_loop(webgl_window, monkeypatch):
    # The browser calls the handlers outside the event loop: it must wake up to see what they schedule
    wakeups = []
    monkeypatch.setattr(pyglet.app.platform_event_loop, "notify", lambda: wakeups.append(True))
    pressed = []
    webgl_window.push_handlers(on_key_press=lambda symbol, modifiers: pressed.append(symbol))
    try:
        init = to_js({"key": "a", "code": "KeyA"}, dict_converter=Object.fromEntries)
        webgl_window.canvas.dispatchEvent(KeyboardEvent.new("keydown", init))
        webgl_window.canvas.dispatchEvent(KeyboardEvent.new("keyup", init))
    finally:
        webgl_window.pop_handlers()

    assert pressed == [pyglet.window.key.A]
    assert len(wakeups) >= 2
