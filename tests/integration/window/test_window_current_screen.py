"""Current-screen lookup through real windows on the supported test runners."""

from __future__ import annotations

import time

import pyglet
import pytest

from pyglet.display.base import Screen
from tests.annotations import Platform, require_platform


pytestmark = [
    require_platform(Platform.WINDOWS + Platform.OSX + Platform.LINUX),
]


@pytest.fixture
def window():
    win = pyglet.window.Window(width=100, height=100, visible=False)
    try:
        yield win
    finally:
        win.close()


@pytest.mark.parametrize('visible', [False, True])
def test_current_screen_is_an_available_screen(window, visible):
    window.set_visible(visible)
    if pyglet.compat_platform not in Platform.EMSCRIPTEN:
        window.dispatch_events()

    screen = window.get_current_screen()

    assert isinstance(screen, Screen)
    assert screen.display is window.display
    assert screen.get_display_id() in {screen.get_display_id() for screen in window.display.get_screens()}


@pytest.mark.skipif(
    pyglet.options.headless or pyglet.options.wayland or pyglet.compat_platform in Platform.HOST_DRIVEN,
    reason='Requires a desktop window that can be positioned',
)
def test_current_screen_follows_window_location(window):
    target = window.screen
    screens = window.display.get_screens()
    window.set_visible(True)

    # Exercise movement even on single-monitor CI runners. With multiple
    # monitors, move to each one and back without changing the fullscreen target.
    for screen in [*screens, screens[0]]:
        window.set_location(screen.x + screen.width // 2, screen.y + screen.height // 2)
        deadline = time.monotonic() + 3
        while True:
            window.dispatch_events()
            current = window.get_current_screen()
            if current.get_display_id() == screen.get_display_id():
                break
            assert time.monotonic() < deadline, f'Expected {screen!r}, got {current!r}'
            time.sleep(0.01)

        assert window.screen is target