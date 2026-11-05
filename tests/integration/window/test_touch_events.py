"""Touch event integration with the window dispatcher."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pyglet.window import BaseWindow
from tests.annotations import Platform, require_platform


@pytest.fixture
def touch_window() -> BaseWindow:
    window = object.__new__(BaseWindow)
    window._touch_positions = {}
    window.dispatch_event = Mock()
    return window


def test_touch_movement_and_pinch_scale(touch_window: BaseWindow) -> None:
    assert touch_window._update_touch_position(1, 10, 10) == (0, 0, 1.0)
    assert touch_window._update_touch_position(2, 20, 10) == (0, 0, 1.0)
    assert touch_window._update_touch_position(1, 5, 10) == (-5, 0, 1.5)
    assert touch_window._update_touch_position(2, 30, 10) == (10, 0, pytest.approx(5 / 3))


def test_touch_end_dispatches_final_movement_and_removes_contact(touch_window: BaseWindow) -> None:
    touch_window._dispatch_touch_event('on_touch_start', 1, 1.5, 2.5, 0, 0, 0.0)
    touch_window._dispatch_touch_event('on_touch_end', 1, 2.0, 3.5, 4, 5, 0.5)

    touch_window.dispatch_event.assert_called_with('on_touch_end', 1, 2.0, 3.5, 0.5, 1.0, 4, 5, 0.5, 1.0)
    assert touch_window._touch_positions == {}
    assert touch_window._update_touch_position(1, 20, 30) == (0, 0, 1.0)


def test_coincident_contacts_do_not_divide_by_zero(touch_window: BaseWindow) -> None:
    touch_window._update_touch_position(1, 10, 10)
    touch_window._update_touch_position(2, 10, 10)
    assert touch_window._update_touch_position(2, 20, 10) == (10, 0, 1.0)


def test_touch_events_are_registered() -> None:
    assert {'on_touch_start', 'on_touch_move', 'on_touch_end'} <= set(BaseWindow.event_types)


@require_platform(Platform.WINDOWS)
def test_dark_mode_update_still_calls_dwm(monkeypatch: pytest.MonkeyPatch) -> None:
    from pyglet.window import win32

    set_attribute = Mock()
    monkeypatch.setattr(win32._dwmapi, 'DwmSetWindowAttribute', set_attribute)
    window = SimpleNamespace(_hwnd=123)

    win32.Win32Window._update_light_mode(window, True)

    set_attribute.assert_called_once()
    assert set_attribute.call_args.args[:2] == (123, win32.constants.DWMWA_USE_IMMERSIVE_DARK_MODE)
    assert set_attribute.call_args.args[2]._obj.value == 0
