"""XInput2 capability negotiation and touch masks with native libraries stubbed out."""
from __future__ import annotations

import importlib.util
import sys
from ctypes import Structure, c_ulong
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pyglet.lib
import pyglet.libs.linux.x11
import pytest


@pytest.fixture
def xinput2(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    xlib = ModuleType('pyglet.libs.linux.x11.xlib')
    xlib.Display = type('Display', (Structure,), {})
    xlib.Time = c_ulong
    xlib.Window = c_ulong
    monkeypatch.setitem(sys.modules, xlib.__name__, xlib)
    monkeypatch.setattr(pyglet.libs.linux.x11, 'xlib', xlib, raising=False)
    library = SimpleNamespace(XIQueryVersion=Mock(), XISelectEvents=Mock())
    monkeypatch.setattr(pyglet.lib, 'load_library', Mock(return_value=library))
    path = Path(__file__).resolve().parents[2] / 'pyglet/libs/linux/x11/xinput2.py'
    spec = importlib.util.spec_from_file_location('_test_xinput2', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_touch_mask_selects_only_begin_update_and_end(xinput2: ModuleType) -> None:
    mask, event_mask = xinput2.touch_event_mask()

    assert event_mask.deviceid == xinput2.XI_ALL_DEVICES
    assert event_mask.mask_len == 3
    assert list(mask) == [0, 0, 0b11100]
    assert [event_mask.mask[index] for index in range(3)] == list(mask)


@pytest.mark.parametrize(('status', 'version', 'supported'), [
    (0, (2, 2), True), (0, (2, 4), True), (0, (2, 1), False), (1, (2, 2), False),
])
def test_query_version_requires_success_and_touch_support(
    xinput2: ModuleType, status: int, version: tuple[int, int], supported: bool,
) -> None:
    display = object()

    def query_version(native_display: object, major: object, minor: object) -> int:
        assert native_display is display
        assert (major._obj.value, minor._obj.value) == (2, 2)
        major._obj.value, minor._obj.value = version
        return status

    xinput2.XIQueryVersion.side_effect = query_version

    assert xinput2.query_version(display) is supported
