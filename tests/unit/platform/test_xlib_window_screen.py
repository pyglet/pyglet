"""Window-to-monitor lookup on X11, without a running X server."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

if sys.platform != "linux":
    pytest.skip("X11-only tests", allow_module_level=True)

from pyglet.window.xlib import XlibWindow


@pytest.fixture
def window(monkeypatch):
    left = SimpleNamespace(x=0, y=0, width=1920, height=1080)
    right = SimpleNamespace(x=1920, y=0, width=1920, height=1080)
    window = object.__new__(XlibWindow)
    window._display = SimpleNamespace(get_screens=lambda: [left, right])
    window._screen = left
    window._fullscreen = False
    window._window = object()
    window._width = 400
    window._height = 200
    window._test_location = (100, 100)
    monkeypatch.setattr(XlibWindow, "get_location", lambda self: self._test_location)
    return window, left, right


def test_windowed_screen_lookup_follows_window_movement(window):
    win, left, right = window

    assert win.get_current_screen() is left
    win._test_location = (2100, 100)
    assert win.get_current_screen() is right
    # Keep the configured fullscreen target unchanged.
    assert win.screen is left


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        ((1600, 100), "left"),   # More window area on the left.
        ((1800, 100), "right"),  # More window area on the right.
        ((1920, 100), "right"),  # Exactly at the second monitor's edge.
        ((4100, 100), "left"),   # Off both monitors; keep configured target.
    ],
)
def test_windowed_screen_lookup_overlap_and_fallback(window, position, expected):
    win, left, right = window
    win._test_location = position

    assert win.get_current_screen() is (left if expected == "left" else right)


def test_windowed_screen_lookup_handles_negative_monitor_coordinates(window):
    win, left, _ = window
    other = SimpleNamespace(x=-1280, y=-200, width=1280, height=1024)
    win._display = SimpleNamespace(get_screens=lambda: [left, other])
    win._test_location = (-1000, 10)

    assert win.get_current_screen() is other


def test_windowed_screen_lookup_uses_framebuffer_dimensions(window, monkeypatch):
    win, _, right = window
    win._test_location = (1780, 100)
    win._width = 500
    monkeypatch.setattr(XlibWindow, "get_size", lambda self: (100, 100))

    # get_size can return logical dimensions under DPI scaling. X11
    # coordinates and monitor geometry need the actual framebuffer width.
    assert win.get_current_screen() is right


@pytest.mark.parametrize("fullscreen,created", [(True, True), (False, False)])
def test_windowed_screen_lookup_keeps_configured_target_without_position(window, fullscreen, created, monkeypatch):
    win, left, _ = window
    win._fullscreen = fullscreen
    if not created:
        win._window = None

    def fail_if_queried(self):
        raise AssertionError("Window position must not be queried")

    monkeypatch.setattr(XlibWindow, "get_location", fail_if_queried)
    assert win.get_current_screen() is left
