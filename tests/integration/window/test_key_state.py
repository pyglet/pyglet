"""Exercise modifier polling through the desktop window backends."""
# ruff: noqa: PLC0415, SLF001
# Each test imports only its own native libraries and targets the test window's native handle.
from __future__ import annotations

from ctypes import byref
from typing import TYPE_CHECKING

import pyglet
import pytest
from pyglet.window import Window, key

from tests.annotations import Platform, require_platform

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.skipif(pyglet.options.headless, reason='requires a desktop window backend')


@pytest.fixture
def keyboard_window() -> Iterator[tuple[Window, key.KeyStateHandler]]:
    window = Window(width=64, height=64, visible=False)
    try:
        keys = key.KeyStateHandler()
        window.push_handlers(keys)
        yield window, keys
    finally:
        window.close()


@require_platform(Platform.WINDOWS)
def test_win32_control_messages(keyboard_window: tuple[Window, key.KeyStateHandler]) -> None:
    from ctypes import WinDLL, c_ssize_t
    from ctypes.wintypes import HWND, LPARAM, UINT, WPARAM

    from pyglet.libs.win32 import constants

    window, keys = keyboard_window
    send_message = WinDLL('user32').SendMessageW
    send_message.argtypes = (HWND, UINT, WPARAM, LPARAM)
    send_message.restype = c_ssize_t
    for bit_flags, left_down, right_down in (
        (0, True, False),
        (1 << 24, True, True),
        ((1 << 30) | (1 << 31), False, True),
        ((1 << 24) | (1 << 30) | (1 << 31), False, False),
    ):
        msg = constants.WM_KEYUP if bit_flags & (1 << 31) else constants.WM_KEYDOWN
        send_message(window._hwnd, msg, constants.VK_CONTROL, 1 | (0x1D << 16) | bit_flags)
        window.dispatch_events()
        assert keys[key.LCTRL] is left_down
        assert keys[key.RCTRL] is right_down
        assert bool(keys.modifiers & key.MOD_CTRL) is (left_down or right_down)


@require_platform(Platform.OSX)
def test_cocoa_shift_flags_changed(keyboard_window: tuple[Window, key.KeyStateHandler]) -> None:
    from pyglet.libs.darwin import cocoapy, quartzkey
    from pyglet.libs.darwin.cocoapy import lib_appkit as appkit

    window, keys = keyboard_window
    left = appkit.NSLeftShiftKeyMask
    right = appkit.NSRightShiftKeyMask
    event_class = cocoapy.ObjCClass('NSEvent')
    with cocoapy.AutoReleasePool():
        empty = cocoapy.get_NSString('')
        for keycode, sides, left_down, right_down in (
            (quartzkey.QZ_LSHIFT, left, True, False),
            (quartzkey.QZ_RSHIFT, left | right, True, True),
            (quartzkey.QZ_LSHIFT, right, False, True),
            (quartzkey.QZ_RSHIFT, 0, False, False),
        ):
            flags = sides | appkit.NSShiftKeyMask if sides else 0
            event = event_class.keyEventWithType_location_modifierFlags_timestamp_windowNumber_context_characters_charactersIgnoringModifiers_isARepeat_keyCode_(
                appkit.NSFlagsChanged, cocoapy.NSPoint(0, 0), flags, 0.0,
                window._nswindow.windowNumber(), None, empty, empty, False, keycode,
            )
            assert event is not None
            window._nsview.flagsChanged_(event)
            window.dispatch_pending_events()
            assert keys[key.LSHIFT] is left_down
            assert keys[key.RSHIFT] is right_down
            assert bool(keys.modifiers & key.MOD_SHIFT) is (left_down or right_down)


@require_platform(Platform.LINUX)
@pytest.mark.skipif(pyglet.options.wayland, reason='requires the Xlib window backend')
def test_xlib_shift_events(keyboard_window: tuple[Window, key.KeyStateHandler]) -> None:
    from pyglet.libs.linux.x11 import xlib

    window, keys = keyboard_window
    display = window._x_display
    for event_type, symbol, state, left_down, right_down in (
        (xlib.KeyPress, key.LSHIFT, 0, True, False),
        (xlib.KeyPress, key.RSHIFT, xlib.ShiftMask, True, True),
        (xlib.KeyRelease, key.LSHIFT, xlib.ShiftMask, False, True),
        (xlib.KeyRelease, key.RSHIFT, xlib.ShiftMask, False, False),
    ):
        event = xlib.XEvent()
        event.xkey.type = event_type
        event.xkey.display = display
        event.xkey.window = window._x_window
        event.xkey.root = window._get_root()
        event.xkey.same_screen = True
        event.xkey.keycode = xlib.XKeysymToKeycode(display, symbol)
        event.xkey.state = state
        assert event.xkey.keycode
        mask = xlib.KeyPressMask if event_type == xlib.KeyPress else xlib.KeyReleaseMask
        assert xlib.XSendEvent(display, event.xkey.window, False, mask, byref(event))
        xlib.XSync(display, False)
        window.dispatch_events()
        assert keys[key.LSHIFT] is left_down
        assert keys[key.RSHIFT] is right_down
        assert bool(keys.modifiers & key.MOD_SHIFT) is (left_down or right_down)
