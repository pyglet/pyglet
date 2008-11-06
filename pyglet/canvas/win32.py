#!/usr/bin/python
# $Id:$

from base import Display, Screen, ScreenMode, Canvas

from pyglet.libs.win32 import _kernel32, _user32, types, constants
from pyglet.libs.win32.constants import *
from pyglet.libs.win32.types import *

class Win32Display(Display):
    def get_screens(self):
        screens = []
        def enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            r = lprcMonitor.contents
            width = r.right - r.left
            height = r.bottom - r.top
            screens.append(
                Win32Screen(self, hMonitor, r.left, r.top, width, height))
            return True
        enum_proc_type = WINFUNCTYPE(BOOL, HMONITOR, HDC, POINTER(RECT), LPARAM)
        enum_proc_ptr = enum_proc_type(enum_proc)
        _user32.EnumDisplayMonitors(NULL, NULL, enum_proc_ptr, 0)
        return screens

class Win32Screen(Screen):
    def __init__(self, display, handle, x, y, width, height):
        super(Win32Screen, self).__init__(display, x, y, width, height)
        self._handle = handle

    def get_matching_configs(self, template):
        canvas = Win32Canvas(self.display, 0, _user32.GetDC(0))
        configs = template.match(canvas)
        # XXX deprecate config's being screen-specific
        for config in configs:
            config.screen = self
        return configs

    def get_modes(self):
        info = MONITORINFOEX()
        info.cbSize = sizeof(MONITORINFOEX)
        _user32.GetMonitorInfoW(self._handle, byref(info))
        device_name = info.szDevice

        i = 0
        modes = []
        while True:
            mode = DEVMODE()
            mode.dmSize = sizeof(DEVMODE)
            r = _user32.EnumDisplaySettingsW(device_name, i, byref(mode))
            if not r:
                break

            modes.append(Win32ScreenMode(self, mode))
            i += 1

        return modes

class Win32ScreenMode(ScreenMode):
    def __init__(self, screen, mode):
        super(Win32ScreenMode, self).__init__(screen)
        self._mode = mode
        self.width = mode.dmPelsWidth
        self.height = mode.dmPelsHeight
        self.depth = mode.dmBitsPerPel
        self.rate = mode.dmDisplayFrequency

class Win32Canvas(Canvas):
    def __init__(self, display, hwnd, hdc):
        super(Win32Canvas, self).__init__(display)
        self.hwnd = hwnd
        self.hdc = hdc

