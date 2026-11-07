"""XInput2 capability negotiation and touch masks with native libraries stubbed out."""
from __future__ import annotations

import importlib.util
import sys
from ctypes import POINTER, Structure, c_double, c_ubyte, c_ulong
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


def test_available_xinput2_reports_loaded_library(xinput2: ModuleType) -> None:
    assert xinput2.is_available()


@pytest.mark.parametrize(('status', 'version', 'expected'), [
    (0, (2, 0), (2, 0)), (0, (2, 1), (2, 1)), (0, (2, 2), (2, 2)),
    (0, (2, 4), (2, 4)), (1, (2, 2), None),
])
def test_get_version_negotiates_server_version(
    xinput2: ModuleType, status: int, version: tuple[int, int], expected: tuple[int, int] | None,
) -> None:
    display = object()

    def query_version(native_display: object, major: object, minor: object) -> int:
        assert native_display is display
        assert (major._obj.value, minor._obj.value) == (2, 2)
        major._obj.value, minor._obj.value = version
        return status

    xinput2.XIQueryVersion.side_effect = query_version

    assert xinput2.get_version(display) == expected


@pytest.mark.parametrize('enabled', [False, True])
def test_raw_motion_mask_selects_master_devices_without_touch_events(xinput2: ModuleType, enabled: bool) -> None:
    mask, event_mask = xinput2.raw_motion_event_mask(enabled)

    assert event_mask.deviceid == xinput2.XI_ALL_MASTER_DEVICES
    assert event_mask.mask_len == 3
    assert list(mask) == [0, 0, 2 if enabled else 0]
    assert [event_mask.mask[index] for index in range(3)] == list(mask)


@pytest.mark.parametrize(('axes', 'values', 'expected'), [
    (0b11, (1.25, -2.5), (1.25, -2.5)),
    (0b01, (-3.5,), (-3.5, 0.0)),
    (0b10, (4.75,), (0.0, 4.75)),
    (0b1010, (-1.5, 100.0), (0.0, -1.5)),
    (0b1100, (10.0, 20.0), (0.0, 0.0)),
    (0, (), (0.0, 0.0)),
])
def test_raw_motion_decodes_sparse_unaccelerated_valuators(
    xinput2: ModuleType, axes: int, values: tuple[float, ...], expected: tuple[float, float],
) -> None:
    mask = (c_ubyte * 1)(axes)
    raw_values = (c_double * len(values))(*values)
    accelerated = (c_double * len(values))(*(999.0 for _ in values))
    event = xinput2.XIRawEvent(
        valuators=xinput2.XIValuatorState(1, mask, accelerated), raw_values=raw_values,
    )

    assert xinput2.raw_motion_delta(event) == expected


def test_empty_raw_motion_does_not_dereference_null_pointers(xinput2: ModuleType) -> None:
    assert xinput2.raw_motion_delta(xinput2.XIRawEvent()) == (0.0, 0.0)
    event = xinput2.XIRawEvent(
        valuators=xinput2.XIValuatorState(1, (c_ubyte * 1)(3), POINTER(c_double)()),
    )
    assert xinput2.raw_motion_delta(event) == (0.0, 0.0)
