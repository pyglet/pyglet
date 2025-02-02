from .base import Display, Screen, ScreenMode, Canvas

from pyglet.libs.win32 import _user32, _shcore, _gdi32
from pyglet.libs.win32.constants import (
    CDS_FULLSCREEN,
    DISP_CHANGE_SUCCESSFUL,
    ENUM_CURRENT_SETTINGS,
    WINDOWS_8_1_OR_GREATER,
    WINDOWS_VISTA_OR_GREATER,
    WINDOWS_10_CREATORS_UPDATE_OR_GREATER,
    USER_DEFAULT_SCREEN_DPI,
    LOGPIXELSX,
    LOGPIXELSY,

)
from pyglet.libs.win32.types import (
    DEVMODE,
    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2,
    MONITORINFOEX,
    MONITORENUMPROC,
    PROCESS_PER_MONITOR_DPI_AWARE,
    UINT,
    sizeof,
    byref
)
from pyglet.libs.win32.context_managers import device_context


def set_dpi_awareness():
    """
       Setting DPI varies per Windows version.
       Note: DPI awareness needs to be set before Window, Display, or Screens are initialized.
    """
    if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
        _user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
    elif WINDOWS_8_1_OR_GREATER:  # 8.1 and above allows per monitor DPI.
        _shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    elif WINDOWS_VISTA_OR_GREATER:  # Only System wide DPI
        _user32.SetProcessDPIAware()


set_dpi_awareness()


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
        super().__init__(display, x, y, width, height)
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

    def get_dpi(self):
        if WINDOWS_8_1_OR_GREATER:
            xdpi = UINT()
            ydpi = UINT()
            _shcore.GetDpiForMonitor(self._handle, 0, byref(xdpi), byref(ydpi))
            xdpi, ydpi = xdpi.value, ydpi.value
        else:
            dc = _user32.GetDC(None)
            xdpi = _gdi32.GetDeviceCaps(dc, LOGPIXELSX)
            ydpi = _gdi32.GetDeviceCaps(dc, LOGPIXELSY)
            _user32.ReleaseDC(0, dc)

        return xdpi

    def get_scale(self):
        xdpi = self.get_dpi()
        return xdpi / USER_DEFAULT_SCREEN_DPI

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
        super().__init__(screen)
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
        super().__init__(display)
        self.hwnd = hwnd
        self.hdc = hdc
