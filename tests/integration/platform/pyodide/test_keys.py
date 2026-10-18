from __future__ import annotations

import sys

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from js import KeyboardEvent, Object
from pyodide.ffi import to_js

from pyglet.window import key
from pyglet.window.emscripten import js_key_to_pyglet


def _symbol(js_key: str, code: str) -> int:
    event = KeyboardEvent.new("keydown", to_js({"key": js_key, "code": code}, dict_converter=Object.fromEntries))
    return js_key_to_pyglet(event)[0]


@pytest.mark.parametrize(("js_key", "code", "symbol"), [
    ("1", "Numpad1", key.NUM_1),  # NumLock on
    ("End", "Numpad1", key.NUM_1),  # NumLock off
    ("Enter", "NumpadEnter", key.NUM_ENTER),
    ("+", "NumpadAdd", key.NUM_ADD),
    ("1", "Digit1", key._1),
    ("End", "End", key.END),
    ("Enter", "Enter", key.RETURN),
    ("a", "KeyQ", key.A),  # The character is kept for the other keys (AZERTY layout)
])
def test_numpad_keys_are_reported_as_num_keys(js_key, code, symbol):
    assert _symbol(js_key, code) == symbol
