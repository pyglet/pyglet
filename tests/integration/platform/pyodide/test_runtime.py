from __future__ import annotations

import sys

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

import js  # noqa: F821
import pyodide  # noqa: F821

import pyglet
from pyglet.resource import get_settings_path


def test_runtime_is_pyodide_on_emscripten():
    assert sys.platform == "emscripten"
    assert pyglet.compat_platform == "emscripten"
    assert pyodide.__version__


def test_browser_document_is_available():
    element = js.document.createElement("div")
    element.id = "pyglet-pyodide-platform-test"
    js.document.body.appendChild(element)
    try:
        assert js.document.getElementById(element.id) is not None
    finally:
        element.remove()


def test_settings_path_uses_persistent_browser_mount():
    assert get_settings_path("pyglet-test") == "/data/pyglet-test"
