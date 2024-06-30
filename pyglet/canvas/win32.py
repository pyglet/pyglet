from .base import Display, Screen, ScreenMode, Canvas

from pyglet.libs.win32 import _user32
from pyglet.libs.win32.constants import (
    CDS_FULLSCREEN,
    DISP_CHANGE_SUCCESSFUL,
    ENUM_CURRENT_SETTINGS
)
from pyglet.libs.win32.types import (
    DEVMODE,
    MONITORINFOEX,
    MONITORENUMPROC,
    sizeof,
    byref
)
from pyglet.libs.win32.context_managers import device_context


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

        enum_proc_ptr = MONITORENUMPROC(enum_proc)
        _user32.EnumDisplayMonitors(None, None, enum_proc_ptr, 0)
        return screens


class Win32Screen(Screen):
    _initial_mode = None

    def __init__(self, display, handle, x, y, width, height):
        super(Win32Screen, self).__init__(display, x, y, width, height)
        self._handle = handle

    def get_matching_configs(self, template):
        with device_context(None) as hdc:
            canvas = Win32Canvas(self.display, 0, hdc)
            configs = template.match(canvas)
            # XXX deprecate config's being screen-specific
            for config in configs:
                config.screen = self

        return configs

    def get_device_name(self):
        info = MONITORINFOEX()
        info.cbSize = sizeof(MONITORINFOEX)
        _user32.GetMonitorInfoW(self._handle, byref(info))
        return info.szDevice

    def get_modes(self):
        device_name = self.get_device_name()
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

    def get_mode(self):
        mode = DEVMODE()
        mode.dmSize = sizeof(DEVMODE)
        _user32.EnumDisplaySettingsW(self.get_device_name(),
                                     ENUM_CURRENT_SETTINGS,
                                     byref(mode))
        return Win32ScreenMode(self, mode)

    def set_mode(self, mode):
        assert mode.screen is self

        if not self._initial_mode:
            self._initial_mode = self.get_mode()
        r = _user32.ChangeDisplaySettingsExW(self.get_device_name(),
                                             byref(mode._mode),
                                             None,
                                             CDS_FULLSCREEN,
                                             None)
        if r == DISP_CHANGE_SUCCESSFUL:
            self.width = mode.width
            self.height = mode.height

    def restore_mode(self):
        if self._initial_mode:
            self.set_mode(self._initial_mode)


class Win32ScreenMode(ScreenMode):
    def __init__(self, screen, mode):
        super(Win32ScreenMode, self).__init__(screen)
        self._mode = mode
        self.width = mode.dmPelsWidth
        self.height = mode.dmPelsHeight
        self.depth = mode.dmBitsPerPel
        self.rate = mode.dmDisplayFrequency
        self.scaling = mode.dmDisplayFixedOutput

    def __repr__(self):
        return f'{self.__class__.__name__}(width={self.width!r}, height={self.height!r}, depth={self.depth!r}, rate={self.rate}, scaling={self.scaling})'

class Win32Canvas(Canvas):
    def __init__(self, display, hwnd, hdc):
        super(Win32Canvas, self).__init__(display)
        self.hwnd = hwnd
        self.hdc = hdc
