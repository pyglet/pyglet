import pyglet
import warnings

from .base import Display, Screen, ScreenMode, Canvas


from ctypes import *
from pyglet.libs.egl import egl
from pyglet.libs.egl import eglext


class HeadlessDisplay(Display):

    def __init__(self):
        super().__init__()
        # TODO: fix this placeholder:
        self._screens = [HeadlessScreen(self, 0, 0, 1920, 1080)]

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

    def get_screens(self):
        return self._screens

    def __del__(self):
        egl.eglTerminate(self._display_connection)


class HeadlessCanvas(Canvas):
    def __init__(self, display, egl_surface):
        super().__init__(display)
        self.egl_surface = egl_surface


class HeadlessScreen(Screen):
    def __init__(self, display, x, y, width, height):
        super().__init__(display, x, y, width, height)

    def get_matching_configs(self, template):
        canvas = HeadlessCanvas(self.display, None)
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
