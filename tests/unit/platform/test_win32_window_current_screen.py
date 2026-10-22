"""Current-screen lookup on Windows, without creating a real window."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

if sys.platform != "win32":
    pytest.skip("Windows-only tests", allow_module_level=True)

from pyglet.libs.win32 import _user32, constants
from pyglet.window.win32 import Win32Window


def test_current_screen_matches_the_monitor_from_window(monkeypatch):
    screens = [SimpleNamespace(_handle=1), SimpleNamespace(_handle=2)]
    window = object.__new__(Win32Window)
    window._hwnd = 123
    window._display = SimpleNamespace(get_screens=lambda: screens)

    def monitor_from_window(hwnd, flag):
        assert hwnd == window._hwnd
        assert flag == constants.MONITOR_DEFAULTTONEAREST
        return 2

    monkeypatch.setattr(_user32, "MonitorFromWindow", monitor_from_window)
    assert window.get_current_screen() is screens[1]
