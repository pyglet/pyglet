import pyglet
import warnings

from ctypes import byref
from threading import Event
from collections import namedtuple

from .base import Display, Screen, ScreenMode, Canvas
from pyglet.libs.egl import egl
from pyglet.libs.egl import eglext
from pyglet.libs.wayland.client import Client


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

    def __init__(self):
        super().__init__()
        num_devices = egl.EGLint()
        eglext.eglQueryDevicesEXT(0, None, byref(num_devices))
        if num_devices.value > 0:
            headless_device = pyglet.options['headless_device']
            if headless_device < 0 or headless_device >= num_devices.value:
                raise ValueError(f'Invalid EGL device id: {headless_device}')
            devices = (eglext.EGLDeviceEXT * num_devices.value)()
            eglext.eglQueryDevicesEXT(num_devices.value, devices, byref(num_devices))
            self._display_connection = eglext.eglGetPlatformDisplayEXT(
                eglext.EGL_PLATFORM_DEVICE_EXT, devices[headless_device], None)
        else:
            warnings.warn('No device available for EGL device platform. Using native display type.')
            display = egl.EGLNativeDisplayType()
            self._display_connection = egl.eglGetDisplay(display)

        egl.eglInitialize(self._display_connection, None, None)

        # Create temporary Client connection to query Screen information:
        # TODO: use the new fractional scaling Protocol if available.
        client = Client('/usr/share/wayland/wayland.xml')
        client.sync()

        self._screens = []

        for i, _ in enumerate(client.globals.get('wl_output', [])):
            self._geo = None
            self._modes = []
            self._scale = None
            self._name = None
            self._descript = None
            self._query_done = Event()
            wl_output = client.protocol_dict['wayland'].bind_interface('wl_output', index=i)
            self._mode_enum = wl_output.enums['mode']
            self._transform_enum = wl_output.enums['transform']
            wl_output.set_handler('geometry', self._wl_output_geometry_handler)
            wl_output.set_handler('mode', self._wl_output_mode_handler)
            wl_output.set_handler('scale', self._wl_output_scale_handler)
            wl_output.set_handler('name', self._wl_output_name_handler)
            wl_output.set_handler('description', self._wl_output_description_handler)
            wl_output.set_handler('done', self._wl_output_done_handler)
            client.sync()
            self._query_done.wait()
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
        egl.eglTerminate(self._display_connection)


class WaylandCanvas(Canvas):
    def __init__(self, display, egl_surface):
        super().__init__(display)
        self.egl_surface = egl_surface


class WaylandScreen(Screen):
    def __init__(self, display, geometry, modes, scale, name, description):
        self.name = name
        self.description = description
        self._scale = scale
        self._geo = geometry
        self._modes = modes
        _width_pixels = max(mode.width for mode in self._modes)
        _height_pixels = max(mode.height for mode in self._modes)
        _width_inches = self._geo.physical_width / 25.4
        _height_inches = self._geo.physical_height / 25.4
        _dpi_width = _width_pixels / _width_inches
        _dpi_height = _height_pixels / _height_inches
        self._dpi = (_dpi_width + _dpi_height) / 2
        super().__init__(display, self._geo.x, self._geo.y, _width_pixels, _height_pixels)

    def get_matching_configs(self, template):
        canvas = WaylandCanvas(self.display, None)
        configs = template.match(canvas)
        # XXX deprecate
        for config in configs:
            config.screen = self
        return configs

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
