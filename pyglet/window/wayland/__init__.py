from __future__ import annotations

import ctypes
import mmap
import os
from ctypes import create_string_buffer
from typing import Sequence

import pyglet

from pyglet.event import EventDispatcher
from pyglet.libs.linux.egl import egl
from pyglet.libs.linux.wayland import xkbcommon
from pyglet.window import BaseWindow, _PlatformEventHandler, _ViewEventHandler, key, mouse
from pyglet.libs.linux.wayland.client import Client, Interface
from pyglet.libs.linux.wayland.wayland_egl import *

# Platform event data is single item, so use platform event handler directly.
WaylandEventHandler = _PlatformEventHandler
ViewEventHandler = _ViewEventHandler


# symbol,ctrl -> motion mapping
_motion_map: dict[tuple[int, bool], int] = {
    (key.UP, False): key.MOTION_UP,
    (key.RIGHT, False): key.MOTION_RIGHT,
    (key.DOWN, False): key.MOTION_DOWN,
    (key.LEFT, False): key.MOTION_LEFT,
    (key.RIGHT, True): key.MOTION_NEXT_WORD,
    (key.LEFT, True): key.MOTION_PREVIOUS_WORD,
    (key.HOME, False): key.MOTION_BEGINNING_OF_LINE,
    (key.END, False): key.MOTION_END_OF_LINE,
    (key.PAGEUP, False): key.MOTION_PREVIOUS_PAGE,
    (key.PAGEDOWN, False): key.MOTION_NEXT_PAGE,
    (key.HOME, True): key.MOTION_BEGINNING_OF_FILE,
    (key.END, True): key.MOTION_END_OF_FILE,
    (key.BACKSPACE, False): key.MOTION_BACKSPACE,
    (key.DELETE, False): key.MOTION_DELETE,
    (key.C, True): key.MOTION_COPY,
    (key.V, True): key.MOTION_PASTE,
}

_modifier_map: dict[int, int] = {
    key.LCTRL: key.MOD_CTRL, key.RCTRL: key.MOD_CTRL,
    key.LSHIFT: key.MOD_SHIFT, key.RSHIFT: key.MOD_SHIFT,
    key.LALT: key.MOD_ALT, key.RALT: key.MOD_ALT,
    key.LWINDOWS: key.MOD_WINDOWS, key.RWINDOWS: key.MOD_WINDOWS,
    key.CAPSLOCK: key.MOD_CAPSLOCK,
    key.NUMLOCK: key.MOD_NUMLOCK,
    key.SCROLLLOCK: key.MOD_SCROLLLOCK,
}


class WaylandWindow(BaseWindow):

    egl_display_connection = None
    egl_surface = None

    _protocols = ['/usr/share/wayland/wayland.xml', '/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml']
    client: Client = None
    wl_compositor: Interface
    wl_surface: Interface
    xdg_wm_base: Interface
    wdg_surface: Interface
    xdg_toplevel: Interface
    wl_pointer: Interface

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        self._mouse_buttons = 0
        self._key_modifiers = 0
        self._has_keyboard_focus = False

        self.xkb_context = xkbcommon.xkb_context_new(xkbcommon.enum_xkb_context_flags(xkbcommon.XKB_CONTEXT_NO_FLAGS))
        self.xkb_keymap = None
        self.xkb_state_withmod = None   # updated when modifiers are pressed
        self.xkb_state_default = None   # never gets updated (for reference)
        self._text_buffer = create_string_buffer(4)
        super().__init__(*args, **kwargs)

    def _recreate(self, changes: Sequence[str]) -> None:
        pass

    def flip(self) -> None:
        if self.context:
            self.context.flip()

    def switch_to(self) -> None:
        if self.context:
            self.context.set_current()

    def set_caption(self, caption: str) -> None:
        pass

    def set_minimum_size(self, width: int, height: int) -> None:
        pass

    def set_maximum_size(self, width: int, height: int) -> None:
        pass

    def set_size(self, width: int, height: int) -> None:
        pass

    def get_size(self) -> tuple[int, int]:
        return self._width, self._height

    def set_location(self, x: int, y: int) -> None:
        pass

    def get_location(self) -> None:
        pass

    def activate(self) -> None:
        pass

    def set_visible(self, visible: bool = True) -> None:
        pass

    def minimize(self) -> None:
        pass

    def maximize(self) -> None:
        pass

    def set_vsync(self, vsync: bool) -> None:
        pass

    def set_mouse_platform_visible(self, platform_visible: bool | None = None) -> None:
        pass

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        pass

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        pass

    def get_system_mouse_cursor(self, name: str) -> None:
        pass

    def dispatch_events(self) -> None:
        while self._event_queue:
            EventDispatcher.dispatch_event(self, *self._event_queue.pop(0))

    def dispatch_pending_events(self) -> None:
        pass

    def before_draw(self) -> None:
        pass

    def _create(self) -> None:
        self.egl_display_connection = self.display.display_connection

        self._dpi = self._screen.get_dpi()
        self._scale = self._screen.get_scale() if pyglet.options.dpi_scaling == "stretch" else 1.0

        # if self._fullscreen:
        #     width, height = self.screen.width, self.screen.height
        # else:
        #     width, height = self._width, self._height
        #     self._view_x = self._view_y = 0
        #     if pyglet.options.dpi_scaling in ("scaled", "stretch"):
        #         w, h = self.get_requested_size()
        #         self._width = width = int(w * self.scale)
        #         self._height = height = int(h * self.scale)
        self.client = self.display.client
        self.client.sync()

        self.wl_compositor = self.client.protocol_dict['wayland'].bind_interface('wl_compositor')

        self.wl_surface = self.wl_compositor.create_surface(next(self.client.oid_pool))
        self.wl_surface.set_handler('preferred_buffer_scale', self.wl_surface_preferred_buffer_scale_handler)

        self.xdg_wm_base = self.client.protocol_dict['xdg_shell'].bind_interface('xdg_wm_base')
        self.xdg_wm_base.set_handler('ping', self.xdg_base_ping_handler)

        self.xdg_surface = self.xdg_wm_base.get_xdg_surface(next(self.client.oid_pool), self.wl_surface)
        self.xdg_surface.set_handler('configure', self.xdg_surface_configure_handler)

        self.xdg_toplevel = self.xdg_surface.get_toplevel(next(self.client.oid_pool))
        self.xdg_toplevel.set_handlers(
            configure=self.xdg_toplevel_configure_handler,
            configure_bounds=self.xdg_toplevel_configure_bounds,
            close=self.xdg_toplevel_close_handler,
        )
        self.xdg_toplevel.set_parent(None)
        self.xdg_toplevel.set_app_id(self._caption)

        self.wl_seat = self.client.protocol_dict['wayland'].bind_interface('wl_seat')
        self.wl_pointer = self.wl_seat.get_pointer(next(self.client.oid_pool))
        self.wl_pointer.set_handlers(motion=self.wl_pointer_motion_handler,
                                    button=self.wl_pointer_button_handler,
                                    axis_value120=self.wl_pointer_axis_value120_handler,
                                    enter=self.wl_pointer_enter_handler,
                                    leave=self.wl_pointer_leave_handler)
        # frame', self.wl_pointer_frame_handler)

        self.wl_keyboard = self.wl_seat.get_keyboard(next(self.client.oid_pool))
        self.wl_keyboard.set_handlers(
            keymap=self.wl_keyboard_keymap_handler,
            modifiers=self.wl_keyboard_modifiers_handler,
            key=self.wl_keyboard_key_handler,
            enter=self.wl_keyboard_enter_handler,
            leave=self.wl_keyboard_leave_handler,
        )

        # Used for software render?
        # import os, tempfile
        # fd, name = tempfile.mkstemp()
        # _data_size = self._width * self._height * 4  # width x height x rgba
        # os.write(fd, b'\xee\x33\x33\xee' * self._width * self._height)  # BGRA
        #
        # wl_shm = self.client.protocol_dict['wayland'].bind_interface('wl_shm')
        # wl_shm_pool = wl_shm.create_pool(next(self.client.oid_pool), fd, _data_size)
        # wl_buffer = wl_shm_pool.create_buffer(next(self.client.oid_pool), 0, self._width, self._height,
        #                                       self._width * 4, 0)
        # self.wl_surface.attach(wl_buffer.oid, 0, 0)

        if not self.egl_surface and not self._shadow:
            # An EGL window needs to be created from a Wayland surface,
            egl_window = wl_egl_window_create(self.wl_surface._proxy, self._width, self._height)

            if not egl_window:
                err = egl.eglGetError()
                msg = f"Failed to create EGL wayland window. Error: 0x{err:04x}"
                raise Exception(msg)

            self._assign_config()

            self.egl_surface = egl.eglCreateWindowSurface(
                self.egl_display_connection,
                self.config._egl_config,
                egl_window,
                None,
            )

            if not self.egl_surface:
                err = egl.eglGetError()
                msg = f"Failed to create egl surface. Error: 0x{err:04x}"
                raise Exception(msg)

            # self.canvas = WaylandCanvas(self.display, self.egl_surface)
            self.context.attach(self)
            self.dispatch_event('_on_internal_resize', self._width, self._height)

    # Start Wayland event handlers

    def xdg_base_ping_handler(self, serial):
        """Keep-alive response to the ping event"""
        self.xdg_wm_base.pong(serial)

    def wl_surface_preferred_buffer_scale_handler(self, factor):
        print(f" --> wl_surface scaling: {factor}")

    def xdg_toplevel_configure_handler(self, width, height, states):
        print(" --> xdg_toplevel configure event", width, height, states)

    def xdg_toplevel_configure_bounds(self, width, height):
        print(" --> xdg_toplevel_configure_bounds event", width, height)

    def xdg_toplevel_close_handler(self):
        self.dispatch_event('on_close')

    def xdg_surface_configure_handler(self, *args):
        print(" --> xdg_surface configure event", args)
        self.xdg_surface.ack_configure(args[0])

    def wl_pointer_button_handler(self, serial, time, button, state):
        mouse_button = {0x110: mouse.LEFT,
                        0x111: mouse.RIGHT,
                        0x112: mouse.MIDDLE,
                        0x113: mouse.MOUSE4,
                        0x114: mouse.MOUSE5}[button]

        if self.wl_pointer.enums['button_state'][state].name == 'pressed':
            self._mouse_buttons |= mouse_button
            self.dispatch_event('on_mouse_press', self._mouse_x, self._mouse_y, mouse_button, self._key_modifiers)

        elif self.wl_pointer.enums['button_state'][state].name == 'released':
            self._mouse_buttons &= ~mouse_button
            self.dispatch_event('on_mouse_release', self._mouse_x, self._mouse_y, mouse_button, self._key_modifiers)

    def wl_pointer_motion_handler(self, time, surface_x, surface_y):
        x = surface_x / self._scale
        # TODO: isolate flipped-Y to a single value
        y = self.height - surface_y / self._scale
        dx = x - self._mouse_x
        dy = y - self._mouse_y
        self._mouse_x = x
        self._mouse_y = y

        if self._mouse_buttons:
            self.dispatch_event('on_mouse_drag', x, y, dx, dy, self._mouse_buttons, self._key_modifiers)
        else:
            self.dispatch_event('on_mouse_motion', x, y, dx, dy)

    def wl_pointer_axis_value120_handler(self, axis, value120):
        # TODO: combine discreet events & dispatch with wl_pointer frame event.
        # 0: vertical axis, 1: horizontal axis
        axis = self.wl_pointer.enums['axis'][axis].value
        scroll_x, scroll_y = {0: (0, -1), 1: (-1, 0)}[axis]
        scroll_x *= (value120 / 120)
        scroll_y *= (value120 / 120)
        self.dispatch_event('on_mouse_scroll', self._mouse_x, self._mouse_y, scroll_x, scroll_y)

    # def wl_pointer_frame_handler(self):
    #     print("end of pointer frame")

    def wl_pointer_enter_handler(self, serial, surface, surface_x, surface_y):
        # TODO: make sure it's the main app surface
        self._mouse_in_window = True
        self.dispatch_event('on_mouse_enter', surface_x, surface_y)

    def wl_pointer_leave_handler(self, serial, surface):
        # TODO: make sure it's the main app surface
        self._mouse_in_window = False
        self.dispatch_event('on_mouse_leave', self._mouse_x, self._mouse_y)

    def wl_keyboard_enter_handler(self, serial, surface, keys):
        # TODO: process held keys?
        self._has_keyboard_focus = True

    def wl_keyboard_leave_handler(self, serial, surface):
        self._has_keyboard_focus = False

    def wl_keyboard_keymap_handler(self, fmt, fd, size):
        # Does not work reliably without mapping:
        mmap_obj = mmap.mmap(fd, size, prot=mmap.PROT_READ, flags=mmap.MAP_PRIVATE)
        data = ctypes.create_string_buffer(mmap_obj.read())
        os.close(fd)

        # Note: There is only one format, so no need to check:
        # fmt = self.wl_keyboard.enums['keymap_format'][fmt].name
        fmt = xkbcommon.enum_xkb_keymap_format(xkbcommon.XKB_KEYMAP_FORMAT_TEXT_V1)
        flags = xkbcommon.enum_xkb_keymap_compile_flags(xkbcommon.XKB_KEYMAP_COMPILE_NO_FLAGS)
        if xkb_keymap := xkbcommon.xkb_keymap_new_from_string(self.xkb_context, data, fmt, flags):
            self.xkb_keymap = xkb_keymap
            self.xkb_state_withmod = xkbcommon.xkb_state_new(self.xkb_keymap)
            self.xkb_state_default = xkbcommon.xkb_state_new(self.xkb_keymap)

    def wl_keyboard_modifiers_handler(self, serial, mods_depressed, mods_latched, mods_locked, group):
        xkbcommon.xkb_state_update_mask(
            self.xkb_state_withmod, mods_depressed, mods_latched, mods_locked, group, group, group)

    def wl_keyboard_key_handler(self, serial, time, keycode, state):
        keycode += 8    # xkbcommon expects +8
        symbol = xkbcommon.xkb_state_key_get_one_sym(self.xkb_state_default, keycode)
        modifier = _modifier_map.get(symbol, 0)

        # released	0, pressed	1, repeated  2
        state_name = self.wl_keyboard.enums['key_state'][state].name

        if state_name == 'pressed':
            _size = xkbcommon.xkb_state_key_get_utf8(self.xkb_state_withmod, keycode, self._text_buffer, 4)
            character = self._text_buffer[:_size].decode()

            self.dispatch_event('on_text', character)
            self.dispatch_event('on_key_press', symbol, self._key_modifiers)
            self._key_modifiers |= modifier

            if self._key_modifiers & key.MOD_ALT:
                return

            ctrl = self._key_modifiers & key.MOD_CTRL != 0
            shft = self._key_modifiers & key.MOD_SHIFT != 0
            if motion := _motion_map.get((symbol, ctrl), None):
                if shft:
                    self.dispatch_event('on_text_motion_select', motion)
                else:
                    self.dispatch_event('on_text_motion', motion)

        if state_name == 'released':
            self.dispatch_event('on_key_release', symbol, self._key_modifiers)
            self._key_modifiers &= ~modifier

    # End Wayland event handlers


__all__ = ['WaylandWindow']
