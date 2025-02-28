from __future__ import annotations

from typing import Sequence

from pyglet.display.wayland import WaylandCanvas

from pyglet.window import key
from pyglet.window import mouse
from pyglet.event import EventDispatcher
from pyglet.libs.egl import egl
from pyglet.libs.wayland.client import Client, Interface
from pyglet.window import (
    BaseWindow,
    DefaultMouseCursor,  # noqa: F401
    ImageMouseCursor,  # noqa: F401
    MouseCursor,  # noqa: F401
    MouseCursorException,  # noqa: F401
    NoSuchDisplayException,  # noqa: F401
    WindowException,  # noqa: F401
    _PlatformEventHandler,
    _ViewEventHandler,
)

# Platform event data is single item, so use platform event handler directly.
WaylandEventHandler = _PlatformEventHandler
ViewEventHandler = _ViewEventHandler


class WaylandWindow(BaseWindow):
    _egl_display_connection = None
    _egl_surface = None

    _protocols = ['/usr/share/wayland/wayland.xml', '/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml']
    client: Client = None
    wl_compositor: Interface
    wl_surface: Interface
    xdg_wm_base: Interface
    wdg_surface: Interface
    xdg_toplevel: Interface
    wl_pointer: Interface

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

    def _create(self) -> None:
        self._egl_display_connection = self.display._display_connection  # noqa: SLF001

        if not self._egl_surface:
            pbuffer_attribs = (egl.EGL_WIDTH, self._width, egl.EGL_HEIGHT, self._height, egl.EGL_NONE)
            pbuffer_attrib_array = (egl.EGLint * len(pbuffer_attribs))(*pbuffer_attribs)
            self._egl_surface = egl.eglCreatePbufferSurface(self._egl_display_connection,
                                                            self.config._egl_config,  # noqa: SLF001
                                                            pbuffer_attrib_array)

            self.canvas = WaylandCanvas(self.display, self._egl_surface)

            self.context.attach(self.canvas)

            self.dispatch_event('_on_internal_resize', self._width, self._height)

        if not self.client:
            self.client = Client(*self._protocols)
            self.client.sync()

            self.wl_compositor = self.client.protocol_dict['wayland'].bind_interface('wl_compositor')

            self.wl_surface = self.wl_compositor.create_surface(next(self.client.oid_pool))
            self.wl_surface.set_handler('preferred_buffer_scale', self.wl_surface_preferred_buffer_scale_handler)

            self.xdg_wm_base = self.client.protocol_dict['xdg_shell'].bind_interface('xdg_wm_base')
            self.xdg_wm_base.set_handler('ping', self.xdg_base_ping_handler)

            self.xdg_surface = self.xdg_wm_base.get_xdg_surface(next(self.client.oid_pool), self.wl_surface.oid)
            self.xdg_surface.set_handler('configure', self.xdg_surface_configure_handler)

            self.xdg_toplevel = self.xdg_surface.get_toplevel(next(self.client.oid_pool))
            self.xdg_toplevel.set_handler('configure', self.xdg_toplevel_configure_handler)
            self.xdg_toplevel.set_handler('close', self.xdg_toplevel_close_handler)
            self.xdg_toplevel.set_parent(None)

            self.wl_seat = self.client.protocol_dict['wayland'].bind_interface('wl_seat')
            self.wl_pointer = self.wl_seat.get_pointer(next(self.client.oid_pool))
            self.wl_pointer.set_handler('motion', self.wl_pointer_motion_handler)
            self.wl_pointer.set_handler('button', self.wl_pointer_button_handler)
            self.wl_pointer.set_handler('enter', self.wl_pointer_enter_handler)
            self.wl_pointer.set_handler('leave', self.wl_pointer_leave_handler)

            # TODO: remove temporary SHM surface:
            import os, tempfile
            fd, name = tempfile.mkstemp()
            _data_size = self._width * self._height * 4  # width x height x rgba
            os.write(fd, b'\xee\x33\x33\xee' * self.width * self.height)  # BGRA

            wl_shm = self.client.protocol_dict['wayland'].bind_interface('wl_shm')
            wl_shm_pool = wl_shm.create_pool(next(self.client.oid_pool), fd, _data_size)
            wl_buffer = wl_shm_pool.create_buffer(next(self.client.oid_pool), 0, self.width, self.height,
                                                  self.width * 4, 0)
            self.wl_surface.attach(wl_buffer.oid, 0, 0)
            self.wl_surface.commit()

    # Start Wayland event handlers

    def xdg_base_ping_handler(self, serial):
        """Keep-alive response to the ping event"""
        self.xdg_wm_base.pong(serial)

    def wl_surface_preferred_buffer_scale_handler(self, factor):
        print(f" --> wl_surface scaling: {factor}")

    def xdg_toplevel_configure_handler(self, width, height, states):
        print(" --> xdg_toplevel configure event", width, height, states)

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

        state_name = self.wl_pointer.enums['button_state'][state].name
        event_name = {'pressed': 'on_mouse_press', 'released': 'on_mouse_release'}[state_name]
        self.dispatch_event(event_name, self._mouse_x, self._mouse_y, mouse_button, 0)

    def wl_pointer_motion_handler(self, time, surface_x, surface_y):
        self._mouse_x = surface_x
        self._mouse_y = surface_y

    def wl_pointer_enter_handler(self, serial, surface, surface_x, surface_y):
        # TODO: make sure it's the main app surface
        self._mouse_in_window = True
        self.dispatch_event('on_mouse_enter', surface_x, surface_y)

    def wl_pointer_leave_handler(self, serial, surface):
        # TODO: make sure it's the main app surface
        self._mouse_in_window = False
        self.dispatch_event('on_mouse_leave', self._mouse_x, self._mouse_y)

    # End Wayland event handlers


__all__ = ['WaylandWindow']
