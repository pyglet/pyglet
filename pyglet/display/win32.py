from __future__ import annotations

import ctypes
from ctypes import byref, sizeof
from typing import TYPE_CHECKING

from pyglet.libs.win32 import _gdi32, _user32
from pyglet.libs.win32.constants import (
    CDS_FULLSCREEN,
    DISP_CHANGE_SUCCESSFUL,
    DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME,
    DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME,
    ENUM_CURRENT_SETTINGS,
    LOGPIXELSX,
    LOGPIXELSY,
    MONITORINFOF_PRIMARY,
    QDC_ONLY_ACTIVE_PATHS,
    USER_DEFAULT_SCREEN_DPI,
    WINDOWS_8_1_OR_GREATER,
    WINDOWS_10_CREATORS_UPDATE_OR_GREATER,
    WINDOWS_VISTA_OR_GREATER,
)
from pyglet.libs.win32.context_managers import device_context
from pyglet.libs.win32.types import (
    DEVMODE,
    DISPLAY_DEVICEW,
    DISPLAYCONFIG_PATH_INFO,
    DISPLAYCONFIG_SOURCE_DEVICE_NAME,
    DISPLAYCONFIG_TARGET_DEVICE_NAME,
    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2,
    MONITORENUMPROC,
    MONITORINFOEX,
    PROCESS_PER_MONITOR_DPI_AWARE,
    UINT,
    UINT32,
)

from .base import Canvas, Display, Screen, ScreenMode

if WINDOWS_8_1_OR_GREATER:
    from pyglet.libs.win32 import _shcore

if TYPE_CHECKING:
    from ctypes.wintypes import HDC, HMONITOR, LPARAM, LPRECT

_ERROR_SUCCESS = 0
_ERROR_INSUFFICIENT_BUFFER = 122

# sizeof(DISPLAYCONFIG_MODE_INFO). Mode data is not used, but the API requires a buffer for it.
_DISPLAYCONFIG_MODE_INFO_SIZE = 64


def set_dpi_awareness() -> None:
    """Setting DPI varies per Windows version.

    .. note:: DPI awareness needs to be set before Window, Display, or Screens are initialized.
    """
    if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
        _user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
    elif WINDOWS_8_1_OR_GREATER:  # 8.1 and above allows per monitor DPI.
        _shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    elif WINDOWS_VISTA_OR_GREATER:  # Only System wide DPI
        _user32.SetProcessDPIAware()


set_dpi_awareness()


class Win32Display(Display):  # noqa: D101
    def get_default_screen(self) -> Screen:
        screens = self.get_screens()
        for screen in screens:
            if screen.is_primary:
                return screen

        return screens[0]

    def get_screens(self) -> list[Win32Screen]:
        screens = []

        def enum_proc(hMonitor: HMONITOR, hdcMonitor: HDC, lprcMonitor: LPRECT, dwData: LPARAM) -> bool:  # noqa: N803, ARG001
            r = lprcMonitor.contents
            width = r.right - r.left
            height = r.bottom - r.top
            screens.append(
                Win32Screen(self, hMonitor, r.left, r.top, width, height))
            return True

        enum_proc_ptr = MONITORENUMPROC(enum_proc)
        _user32.EnumDisplayMonitors(None, None, enum_proc_ptr, 0)
        return screens


class Win32Screen(Screen):  # noqa: D101
    _handle: HMONITOR
    _initial_mode = None

    def __init__(self, display: Win32Display, handle: HMONITOR, x: int, y: int, width: int, height: int) -> None:  # noqa: D107
        super().__init__(display, x, y, width, height)
        self._handle = handle
        self._device_name = self.get_device_name()  # \\.\DISPLAY1
        self._friendly_name = self._get_friendly_name()

    @property
    def is_primary(self) -> bool:
        """If the screen is considered the primary according to the operating system."""
        info = self._get_monitor_info()
        return info.dwFlags & MONITORINFOF_PRIMARY

    @staticmethod
    def _query_active_display_paths() -> list[DISPLAYCONFIG_PATH_INFO]:
        """Query the currently active Display Configuration paths.

        ``GetDisplayConfigBufferSizes`` only reports the sizes required at the moment it is
        called. If the display topology changes before ``QueryDisplayConfig`` runs, the buffers
        may no longer be large enough and it fails with ``ERROR_INSUFFICIENT_BUFFER``. In that
        case the sizes have to be queried again and larger buffers allocated, so each attempt
        re-runs the size query and reallocates.
        """
        while True:
            path_count = UINT32()
            mode_count = UINT32()

            result = _user32.GetDisplayConfigBufferSizes(
                QDC_ONLY_ACTIVE_PATHS,
                ctypes.byref(path_count),
                ctypes.byref(mode_count),
            )
            if result != _ERROR_SUCCESS:
                return []

            paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
            modes = ctypes.create_string_buffer(_DISPLAYCONFIG_MODE_INFO_SIZE * mode_count.value)

            result = _user32.QueryDisplayConfig(
                QDC_ONLY_ACTIVE_PATHS,
                ctypes.byref(path_count),
                paths,
                ctypes.byref(mode_count),
                modes,
                0,
            )
            if result == _ERROR_INSUFFICIENT_BUFFER:
                continue

            if result != _ERROR_SUCCESS:
                return []

            # QueryDisplayConfig may fill in fewer paths than were allocated.
            return paths[:path_count.value]

    def _get_display_config_path(self) -> DISPLAYCONFIG_PATH_INFO | None:
        """Get the active Display Configuration path for this screen."""
        for path in self._query_active_display_paths():
            if not path.targetInfo.targetAvailable:
                continue

            source_name = DISPLAYCONFIG_SOURCE_DEVICE_NAME()
            source_name.header.adapterId = path.sourceInfo.adapterId
            source_name.header.id = path.sourceInfo.id
            source_name.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME
            source_name.header.size = ctypes.sizeof(source_name)

            result = _user32.DisplayConfigGetDeviceInfo(ctypes.byref(source_name.header))
            if result != _ERROR_SUCCESS:
                continue

            if source_name.viewGdiDeviceName.casefold() == self._device_name.casefold():
                return path

        return None

    def _get_friendly_name_display_config_api(self) -> str:
        """Get the friendly name of a monitor using the newer Display Configuration API.

        This API is meant to replace EnumDisplayDevicesW, and should be more accurate.

        Requires Windows Vista or higher.
        """
        path_count = UINT32()
        mode_count = UINT32()

        result = _user32.GetDisplayConfigBufferSizes(
            QDC_ONLY_ACTIVE_PATHS, ctypes.byref(path_count), ctypes.byref(mode_count),
        )
        if result != 0:
            return "Unknown"

        paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
        modes = ctypes.create_string_buffer(64 * mode_count.value)  # dummy buffer

        result = _user32.QueryDisplayConfig(
            QDC_ONLY_ACTIVE_PATHS, ctypes.byref(path_count), paths, ctypes.byref(mode_count), modes, 0,
        )
        if result != 0:
            return "Unknown"

        for i in range(path_count.value):
            path = paths[i]

            source_name = DISPLAYCONFIG_SOURCE_DEVICE_NAME()
            source_name.header.adapterId = path.sourceInfo.adapterId
            source_name.header.id = path.sourceInfo.id
            source_name.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME
            source_name.header.size = ctypes.sizeof(source_name)

            result = _user32.DisplayConfigGetDeviceInfo(ctypes.byref(source_name.header))
            if result != 0:
                continue

            if source_name.viewGdiDeviceName != self._device_name:
                continue

            if not path.targetInfo.targetAvailable:
                  continue

            target_name = DISPLAYCONFIG_TARGET_DEVICE_NAME()

            target_name.header.adapterId = path.targetInfo.adapterId
            target_name.header.id = path.targetInfo.id
            target_name.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
            target_name.header.size = ctypes.sizeof(target_name)

            if _user32.DisplayConfigGetDeviceInfo(ctypes.byref(target_name.header)) == 0:
                return target_name.monitorFriendlyDeviceName

        return "Unknown"

    def _get_refresh_rate_display_config_api(self) -> float | None:
        """Get the precise refresh rate of the current display path."""
        path = self._get_display_config_path()
        if path is None:
            return None

        refresh_rate = path.targetInfo.refreshRate
        numerator = int(refresh_rate.Numerator)
        denominator = int(refresh_rate.Denominator)
        if numerator <= 0 or denominator <= 0:
            return None
        rate = numerator / denominator
        return rate if rate >= 1 else None

    def _get_friendly_name(self) -> str:
        if WINDOWS_VISTA_OR_GREATER:
            return self._get_friendly_name_display_config_api()

        dd = DISPLAY_DEVICEW()
        dd.cb = ctypes.sizeof(dd)
        if _user32.EnumDisplayDevicesW(self._device_name, 0, ctypes.byref(dd), 0):
            return dd.DeviceString

        return "Unknown"

    def get_matching_configs(self, template):
        with device_context(None) as hdc:
            canvas = Win32Canvas(self.display, 0, hdc)
            configs = template.match(canvas)
            # XXX deprecate config's being screen-specific
            for config in configs:
                config.screen = self

        return configs

    def _get_monitor_info(self) -> MONITORINFOEX:
        info = MONITORINFOEX()
        info.cbSize = sizeof(MONITORINFOEX)
        _user32.GetMonitorInfoW(self._handle, byref(info))
        return info

    def get_display_id(self) -> str:
        return self._device_name

    def get_monitor_name(self) -> str:
        return self._friendly_name

    def get_device_name(self) -> str:
        info = self._get_monitor_info()
        return info.szDevice

    def get_dpi(self) -> int:
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

    def get_scale(self) -> float:
        xdpi = self.get_dpi()
        return xdpi / USER_DEFAULT_SCREEN_DPI

    def get_modes(self) -> list[Win32ScreenMode]:
        device_name = self.get_device_name()
        current_mode = self.get_mode()
        i = 0
        modes = []
        while True:
            mode = DEVMODE()
            mode.dmSize = sizeof(DEVMODE)
            r = _user32.EnumDisplaySettingsW(device_name, i, byref(mode))
            if not r:
                break

            rate = current_mode.rate if self._same_mode(mode, current_mode._mode) else None
            modes.append(Win32ScreenMode(self, mode, rate))
            i += 1

        return modes

    def get_mode(self) -> Win32ScreenMode:
        mode = DEVMODE()
        mode.dmSize = sizeof(DEVMODE)
        _user32.EnumDisplaySettingsW(self.get_device_name(),
                                     ENUM_CURRENT_SETTINGS,
                                     byref(mode))
        rate = self._get_refresh_rate_display_config_api() if WINDOWS_VISTA_OR_GREATER else None
        return Win32ScreenMode(self, mode, rate)

    @staticmethod
    def _same_mode(first: DEVMODE, second: DEVMODE) -> bool:
        """Return whether two legacy mode records describe the same mode."""
        return (
            first.dmPelsWidth == second.dmPelsWidth
            and first.dmPelsHeight == second.dmPelsHeight
            and first.dmBitsPerPel == second.dmBitsPerPel
            and first.dmDisplayFrequency == second.dmDisplayFrequency
        )

    def set_mode(self, mode: Win32ScreenMode) -> None:
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

    def restore_mode(self) -> None:
        if self._initial_mode:
            self.set_mode(self._initial_mode)


_win32_scale_name = {
    0: "default",
    1: "center",
    2: "stretch",
}
class Win32ScreenMode(ScreenMode):  # noqa: D101
    def __init__(self, screen: Win32Screen, mode: DEVMODE, rate: float | None = None) -> None:  # noqa: D107
        super().__init__(screen)
        self._mode = mode
        self.width = mode.dmPelsWidth
        self.height = mode.dmPelsHeight
        self.depth = mode.dmBitsPerPel
        self.rate = rate if rate is not None else mode.dmDisplayFrequency
        self.scaling = mode.dmDisplayFixedOutput

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}(width={self.width!r}, height={self.height!r}, depth={self.depth!r},'
                f'rate={self.rate}, scaling={_win32_scale_name.get(self.scaling)})')

class Win32Canvas(Canvas):  # noqa: D101
    def __init__(self, display: Win32Display, hwnd: HWND, hdc: HDC) -> None:  # noqa: D107
        super().__init__(display)
        self.hwnd = hwnd
        self.hdc = hdc
