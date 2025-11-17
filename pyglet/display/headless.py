from __future__ import annotations

from typing import Literal

import warnings
from ctypes import byref

import pyglet

from .base import Display, Screen
from pyglet.libs import egl
from pyglet.util import debug_print

_debug = debug_print('debug_api')


class HeadlessDisplay(Display):

    def __init__(self):
        super().__init__()
        # TODO: fix this placeholder:
        self._screens = [HeadlessScreen(self, 0, 0, 1920, 1080)]

        num_devices = egl.EGLint()
        try:
            egl.eglQueryDevicesEXT(0, None, byref(num_devices))
        except pyglet.libs.egl.eglext.MissingFunctionException:
            warnings.warn('No device available for EGL device platform. Using native display type.')
            display = egl.EGLNativeDisplayType()
            self._display_connection = egl.eglGetDisplay(display)

        if num_devices.value > 0:
            headless_device = pyglet.options.headless_device
            if headless_device < 0 or headless_device >= num_devices.value:
                raise ValueError(f'Invalid EGL device id: {headless_device}')
            devices = (egl.EGLDeviceEXT * num_devices.value)()
            egl.eglQueryDevicesEXT(num_devices.value, devices, byref(num_devices))
            self._display_connection = egl.eglGetPlatformDisplayEXT(
                egl.EGL_PLATFORM_DEVICE_EXT, devices[headless_device], None,
            )

        majorver = egl.EGLint()
        minorver = egl.EGLint()
        egl.eglInitialize(self._display_connection, majorver, minorver)
        assert _debug(f"EGL version: {majorver.value}.{minorver.value}")

    def get_screens(self):
        return self._screens

    def __del__(self):
        egl.eglTerminate(self._display_connection)


class HeadlessScreen(Screen):
    def __init__(self, display, x, y, width, height):
        super().__init__(display, x, y, width, height)

    def get_modes(self):
        pass

    def get_mode(self):
        pass

    def set_mode(self, mode):
        pass

    def restore_mode(self):
        pass

    def get_display_id(self) -> str | int:
        # No real unique ID is available, just hash together the properties.
        return hash((self.x, self.y, self.width, self.height))

    def get_monitor_name(self) -> str | Literal["Unknown"]:
        return "Headless"
