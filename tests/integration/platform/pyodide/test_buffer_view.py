from __future__ import annotations

import sys

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from pyglet.libs.emscripten import PersistentBufferView


def test_view_survives_webassembly_memory_growth():
    data = bytearray(b"pyglet")
    view = PersistentBufferView(data)
    old_data = view.data

    # Allocate until the WebAssembly memory grows, which detaches the views on it
    allocations = []
    while old_data.buffer.byteLength and len(allocations) < 64:
        allocations.append(bytearray(16 * 1024 * 1024))
    assert old_data.buffer.byteLength == 0, "The WebAssembly memory did not grow"

    try:
        assert view.data.byteLength == len(data)
        assert bytes(view.data.to_py()) == b"pyglet"
        data[0:2] = b"PY"
        assert bytes(view.subarray(0, 2).to_py()) == b"PY"
    finally:
        view.release()
        allocations.clear()
