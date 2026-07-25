from __future__ import annotations

from collections import namedtuple
from threading import Event
from typing import Literal

from pyglet.libs.linux.egl import egl, eglext
from pyglet.libs.linux.wayland.client import Client

from .base import Display, Screen, ScreenMode

ModeInfo = namedtuple('ModeInfo', 'width, height, depth, rate, current, primary')
Geometry = namedtuple('Geometry', 'x, y, physical_width, physical_height, make, model, transform')


class WaylandScreenMode(ScreenMode):
    def __init__(self, screen: Screen, info: ModeInfo):
        self.width = info.width
        self.height = info.height
        self.depth = info.depth
        self.rate = info.rate
        self.primary = info.primary
        self.current = info.current
        super().__init__(screen)


class WaylandDisplay(Display):
    _protocols = ('/usr/share/wayland/wayland.xml', '/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml')
    _display_instance: WaylandDisplay | None = None

    def __new__(cls):
        if cls._display_instance:
            return cls._display_instance
        cls._display_instance = super().__new__(cls)
        return cls._display_instance

    def __init__(self):
        super().__init__()
        # Create temporary Client connection to query Screen information:
        # TODO: use the new fractional scaling Protocol if available.
        self.client = Client(*self._protocols)
        self.client.sync()

        self.display_connection = egl.eglGetPlatformDisplay(eglext.EGL_PLATFORM_WAYLAND, self.client.wl_display_p, None)

        assert egl.eglInitialize(self.display_connection, None, None) == egl.EGL_TRUE, "Failed to initialize Display"

        self._screens = []
        for i, _ in enumerate(self.client.globals.get('wl_output', [])):
            # Initialize values to default
            self._geo = None
            self._modes = []
            self._scale = None
            self._name = None
            self._descript = None
            self._query_done = Event()
            wl_output = self.client.protocol_dict['wayland'].bind_interface('wl_output', index=i)
            self._mode_enum = wl_output.enums['mode']
            self._transform_enum = wl_output.enums['transform']
            # Callbacks will update values:
            wl_output.set_handlers(
                geometry=self._wl_output_geometry_handler,
                mode=self._wl_output_mode_handler,
                scale=self._wl_output_scale_handler,
                name=self._wl_output_name_handler,
                description=self._wl_output_description_handler,
                done=self._wl_output_done_handler,
            )
            self.client.sync()
            self._query_done.wait()
            # Make Screen instance with the now-filled-in values:
            self._screens.append(WaylandScreen(self, self._geo, self._modes, self._scale, self._name, self._descript))
            wl_output.release()

    # Start Wayland Event handlers

    def _wl_output_done_handler(self):
        self._query_done.set()

    def _wl_output_scale_handler(self, scale):
        self._scale = scale

    def _wl_output_name_handler(self, name):
        self._name = name

    def _wl_output_description_handler(self, description):
        self._descript = description

    def _wl_output_geometry_handler(self, x, y, physical_width, physical_height, subpixel, make, model, transform):
        transform = self._transform_enum[transform]
        self._geo = Geometry(x, y, physical_width, physical_height, make, model, transform)

    def _wl_output_mode_handler(self, flags, width, height, refresh):
        is_current = self._mode_enum.entries[0] & flags
        is_primary = self._mode_enum.entries[1] & flags
        self._modes.append(ModeInfo(width, height, None, refresh * 0.001, is_current, is_primary))

    # End Wayland Event handlers

    def get_screens(self):
        return self._screens

    def __del__(self):
        egl.eglTerminate(self.display_connection)


class WaylandScreen(Screen):

    def get_display_id(self) -> str | int:
        return self.name

    def get_monitor_name(self) -> str | Literal["Unknown"]:
        return self.description

    def __init__(self, display, geometry, modes, scale, name, description):
        self.name = name
        self.description = description
        self._scale = scale
        self._geo = geometry
        self._modes = modes
        _width_pixels = max(mode.width for mode in self._modes)
        _height_pixels = max(mode.height for mode in self._modes)
        # No physical size can exist, such as WSL (they are virtual).
        if self._geo.physical_width != 0:
            _width_inches = self._geo.physical_width / 25.4
            _height_inches = self._geo.physical_height / 25.4
            _dpi_width = _width_pixels / _width_inches
            _dpi_height = _height_pixels / _height_inches
            self._dpi = (_dpi_width + _dpi_height) / 2
        else:
            self._dpi = scale

        super().__init__(display, self._geo.x, self._geo.y, _width_pixels, _height_pixels)

    def get_modes(self):
        return self._modes

    def get_mode(self):
        for mode in self._modes:
            if mode.current:
                return mode
        return self._modes[0]

    def set_mode(self, mode):
        pass

    def restore_mode(self):
        pass

    def get_dpi(self):
        return self._dpi

    def get_scale(self):
        return self._scale

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, width={self.width}, height={self.height})"
