import pyglet
import warnings

from ctypes import byref
from threading import Event
from collections import namedtuple

from .base import Display, Screen, ScreenMode, Canvas
from pyglet.libs.egl import egl
from pyglet.libs.egl import eglext
from pyglet.libs.wayland.client import Client


ModeInfo = namedtuple('ModeInfo', 'width, height, depth, rate')


class WaylandScreenMode(ScreenMode):
    def __init__(self, screen: Screen, info: ModeInfo):
        self.width = info.width
        self.height = info.height
        self.depth = info.depth
        self.rate = info.rate
        super().__init__(screen)


class WaylandDisplay(Display):

    def __init__(self):
        super().__init__()
        num_devices = egl.EGLint()
        eglext.eglQueryDevicesEXT(0, None, byref(num_devices))
        if num_devices.value > 0:
            headless_device = pyglet.options['headless_device']
            if headless_device < 0 or headless_device >= num_devices.value:
                raise ValueError(f'Invalid EGL devide id: {headless_device}')
            devices = (eglext.EGLDeviceEXT * num_devices.value)()
            eglext.eglQueryDevicesEXT(num_devices.value, devices, byref(num_devices))
            self._display_connection = eglext.eglGetPlatformDisplayEXT(
                eglext.EGL_PLATFORM_DEVICE_EXT, devices[headless_device], None)
        else:
            warnings.warn('No device available for EGL device platform. Using native display type.')
            display = egl.EGLNativeDisplayType()
            self._display_connection = egl.eglGetDisplay(display)

        egl.eglInitialize(self._display_connection, None, None)

        self.mode_done = Event()

        client = Client('/usr/share/wayland/wayland.xml')
        client.sync()
        self.wl_output = client.protocol_dict['wayland'].bind_interface('wl_output')
        # self.wl_output.set_handler('geometry', self.wl_output_geometry_handler)
        self.wl_output.set_handler('mode', self._wl_output_mode_handler)
        self.wl_output.set_handler('done', self._wl_output_done_handler)
        #
        # self.mode_done.wait()
        self.wl_output.release()

        self._screen_modes = []

        self._screens = [WaylandScreen(self, 0, 0, 1920, 1080)]

    def _wl_output_done_handler(self):
        self.mode_done.set()

    def _wl_output_mode_handler(self, flags, width, height, refresh):
        # mode_enum = self.wl_output.enums['mode']
        # is_current = mode_enum.entries[0] & flags
        # is_primary = mode_enum.entries[1] & flags
        refresh *= 0.001
        modeinfo = ModeInfo(width, height, None, refresh)
        self._screen_modes.append(modeinfo)

    def get_screens(self):
        return self._screens

    def __del__(self):
        egl.eglTerminate(self._display_connection)


class WaylandCanvas(Canvas):
    def __init__(self, display, egl_surface):
        super().__init__(display)
        self.egl_surface = egl_surface


class WaylandScreen(Screen):
    def __init__(self, display, x, y, width, height):
        super().__init__(display, x, y, width, height)

    def get_matching_configs(self, template):
        canvas = WaylandCanvas(self.display, None)
        configs = template.match(canvas)
        # XXX deprecate
        for config in configs:
            config.screen = self
        return configs

    def get_modes(self):
        pass

    def get_mode(self):
        pass

    def set_mode(self, mode):
        pass

    def restore_mode(self):
        pass
