from __future__ import annotations

import sys
from pathlib import Path

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

import js
import pyodide

import pyglet
from pyodide.ffi import run_sync
from pyglet.libs.emscripten.filesystem import sync_storage
from pyglet.resource import get_settings_path
from pyglet.storage import Storage


def test_runtime_is_pyodide_on_emscripten():
    assert sys.platform == "emscripten"
    assert pyglet.compat_platform == "emscripten"
    assert pyodide.__version__ == pyglet.PYODIDE_VERSION


def test_browser_document_is_available():
    element = js.document.createElement("div")
    element.id = "pyglet-pyodide-platform-test"
    js.document.body.appendChild(element)
    try:
        assert js.document.getElementById(element.id) is not None
    finally:
        element.remove()


def test_storage_uses_browser_persistence_mount_points():
    assert get_settings_path("pyglet-test") == "/data/pyglet-test"
    storage = Storage("pyglet-test")
    assert storage.data == Path("/data/pyglet-test")
    assert storage.cache == Path("/cache/pyglet-test")
    cache_file = storage.cache / "cache-test.txt"
    cache_file.write_text("cached")
    run_sync(sync_storage())
    assert cache_file.read_text() == "cached"
