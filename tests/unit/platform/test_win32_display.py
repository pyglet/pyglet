from __future__ import annotations

import ctypes
from types import SimpleNamespace
import sys

import pytest

if sys.platform != 'win32':
    pytest.skip('Win32 display tests require Windows', allow_module_level=True)

from pyglet.display import win32
from pyglet.libs.win32.types import (
    DEVMODE,
    DISPLAYCONFIG_PATH_INFO,
    DISPLAYCONFIG_SOURCE_DEVICE_NAME,
)


def _screen(device_name=r'\\.\DISPLAY1'):
    screen = object.__new__(win32.Win32Screen)
    screen._device_name = device_name
    return screen


def _path(source_id, numerator=120_000, denominator=1_001, available=True):
    path = DISPLAYCONFIG_PATH_INFO()
    path.sourceInfo.id = source_id
    path.targetInfo.id = source_id
    path.targetInfo.targetAvailable = available
    path.targetInfo.refreshRate.Numerator = numerator
    path.targetInfo.refreshRate.Denominator = denominator
    return path


def test_display_config_path_matches_gdi_device_name(monkeypatch):
    paths = (_path(1), _path(2))
    names = {
        1: r'\\.\DISPLAY2',
        2: r'\\.\DISPLAY1',
    }

    def get_buffer_sizes(_flags, path_count, mode_count):
        path_count._obj.value = len(paths)
        mode_count._obj.value = 1
        return 0

    def query_display_config(_flags, path_count, output_paths, _mode_count, _modes, _topology):
        for index, path in enumerate(paths):
            output_paths[index] = path
        path_count._obj.value = len(paths)
        return 0

    def get_device_info(header):
        source = ctypes.cast(
            header,
            ctypes.POINTER(DISPLAYCONFIG_SOURCE_DEVICE_NAME),
        ).contents
        source.viewGdiDeviceName = names[source.header.id]
        return 0

    monkeypatch.setattr(win32._user32, 'GetDisplayConfigBufferSizes', get_buffer_sizes)
    monkeypatch.setattr(win32._user32, 'QueryDisplayConfig', query_display_config)
    monkeypatch.setattr(win32._user32, 'DisplayConfigGetDeviceInfo', get_device_info)

    selected = _screen()._get_display_config_path()

    assert selected is not None
    assert selected.sourceInfo.id == 2


def test_display_config_query_reallocates_after_insufficient_buffer(monkeypatch):
    buffer_sizes = iter(((1, 1), (2, 2)))
    query_results = iter((win32._ERROR_INSUFFICIENT_BUFFER, 0))
    allocations = []

    def get_buffer_sizes(_flags, path_count, mode_count):
        paths, modes = next(buffer_sizes)
        path_count._obj.value = paths
        mode_count._obj.value = modes
        return 0

    def query_display_config(_flags, _path_count, output_paths, _mode_count, modes, _topology):
        allocations.append((len(output_paths), len(modes)))
        return next(query_results)

    monkeypatch.setattr(win32._user32, 'GetDisplayConfigBufferSizes', get_buffer_sizes)
    monkeypatch.setattr(win32._user32, 'QueryDisplayConfig', query_display_config)

    found = win32.Win32Screen._query_active_display_paths()

    # The second attempt must re-query the sizes and allocate the larger buffers.
    assert allocations == [
        (1, win32._DISPLAYCONFIG_MODE_INFO_SIZE),
        (2, 2 * win32._DISPLAYCONFIG_MODE_INFO_SIZE),
    ]
    assert len(found) == 2


def test_display_config_query_failure_yields_no_path(monkeypatch):
    def get_buffer_sizes(_flags, path_count, mode_count):
        path_count._obj.value = 1
        mode_count._obj.value = 1
        return 0

    monkeypatch.setattr(win32._user32, 'GetDisplayConfigBufferSizes', get_buffer_sizes)
    monkeypatch.setattr(win32._user32, 'QueryDisplayConfig', lambda *_args: 5)  # ERROR_ACCESS_DENIED

    assert _screen()._get_display_config_path() is None


@pytest.mark.parametrize(
    ('numerator', 'denominator'),
    [
        (0, 1_001),
        (120_000, 0),
        (1, 2),
    ],
)
def test_refresh_rate_rejects_invalid_rationals(monkeypatch, numerator, denominator):
    monkeypatch.setattr(
        win32.Win32Screen,
        '_get_display_config_path',
        lambda _self: _path(1, numerator, denominator),
    )

    assert _screen()._get_refresh_rate_display_config_api() is None


def test_refresh_rate_preserves_fractional_value(monkeypatch):
    monkeypatch.setattr(
        win32.Win32Screen,
        '_get_display_config_path',
        lambda _self: _path(1),
    )

    assert _screen()._get_refresh_rate_display_config_api() == pytest.approx(
        119.88011988011988,
    )


def test_screen_mode_prefers_precise_rate():
    mode = DEVMODE()
    mode.dmPelsWidth = 3840
    mode.dmPelsHeight = 2160
    mode.dmBitsPerPel = 32
    mode.dmDisplayFrequency = 119

    screen_mode = win32.Win32ScreenMode(_screen(), mode, 120_000 / 1_001)

    assert screen_mode.rate == pytest.approx(119.88011988011988)


def test_screen_mode_falls_back_to_legacy_integer_rate():
    mode = SimpleNamespace(
        dmPelsWidth=3840,
        dmPelsHeight=2160,
        dmBitsPerPel=32,
        dmDisplayFrequency=119,
        dmDisplayFixedOutput=0,
    )

    assert win32.Win32ScreenMode(_screen(), mode).rate == 119


def test_same_mode_includes_legacy_refresh_rate():
    current = DEVMODE()
    current.dmPelsWidth = 3840
    current.dmPelsHeight = 2160
    current.dmBitsPerPel = 32
    current.dmDisplayFrequency = 119

    same = DEVMODE()
    ctypes.memmove(ctypes.byref(same), ctypes.byref(current), ctypes.sizeof(current))
    different_rate = DEVMODE()
    ctypes.memmove(
        ctypes.byref(different_rate),
        ctypes.byref(current),
        ctypes.sizeof(current),
    )
    different_rate.dmDisplayFrequency = 120

    assert win32.Win32Screen._same_mode(current, same)
    assert not win32.Win32Screen._same_mode(current, different_rate)


def test_get_modes_applies_precise_rate_only_to_current_mode(monkeypatch):
    current = DEVMODE()
    current.dmPelsWidth = 3840
    current.dmPelsHeight = 2160
    current.dmBitsPerPel = 32
    current.dmDisplayFrequency = 119

    other = DEVMODE()
    ctypes.memmove(ctypes.byref(other), ctypes.byref(current), ctypes.sizeof(current))
    other.dmDisplayFrequency = 60
    modes = (current, other)

    def enum_display_settings(_device_name, index, output):
        if index >= len(modes):
            return 0
        ctypes.memmove(output, ctypes.byref(modes[index]), ctypes.sizeof(DEVMODE))
        return 1

    screen = _screen()
    precise_rate = 120_000 / 1_001
    monkeypatch.setattr(screen, 'get_device_name', lambda: screen._device_name)
    monkeypatch.setattr(screen, 'get_mode', lambda: win32.Win32ScreenMode(screen, current, precise_rate))
    monkeypatch.setattr(win32._user32, 'EnumDisplaySettingsW', enum_display_settings)

    found = screen.get_modes()

    assert found[0].rate == pytest.approx(119.88011988011988)
    assert found[1].rate == 60
