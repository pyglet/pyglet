from __future__ import annotations

import ctypes
import warnings
from ctypes import POINTER, byref, c_buffer, c_char_p, c_int, cast
from typing import TYPE_CHECKING

import pyglet
from pyglet import app
from pyglet.app.xlib import XlibSelectDevice
from pyglet.libs.x11 import xlib
from pyglet.util import asbytes

from . import xlib_vidmoderestore
from .base import Canvas, Display, Screen, ScreenMode

if TYPE_CHECKING:
    from pyglet.gl import Config

try:
    from pyglet.libs.x11 import xinerama

    _have_xinerama = True
except:
    _have_xinerama = False

try:
    from pyglet.libs.x11 import xsync

    _have_xsync = True
except:
    _have_xsync = False

try:
    from pyglet.libs.x11 import xf86vmode

    _have_xf86vmode = True
except:
    _have_xf86vmode = False

try:
    from pyglet.libs.x11 import xrandr

    _have_xrandr = True
except ImportError:
    _have_xrandr = False


class NoSuchDisplayException(Exception):
    pass


# Set up error handler
def _error_handler(display, event):
    # By default, all errors are silently ignored: this has a better chance
    # of working than the default behaviour of quitting ;-)
    #
    # We've actually never seen an error that was our fault; they're always
    # driver bugs (and so the reports are useless).  Nevertheless, set
    # environment variable PYGLET_DEBUG_X11 to 1 to get dumps of the error
    # and a traceback (execution will continue).
    if pyglet.options['debug_x11']:
        event = event.contents
        buf = c_buffer(1024)
        xlib.XGetErrorText(display, event.error_code, buf, len(buf))
        print('X11 error:', buf.value)
        print('   serial:', event.serial)
        print('  request:', event.request_code)
        print('    minor:', event.minor_code)
        print(' resource:', event.resourceid)

        import traceback

        print('Python stack trace (innermost last):')
        traceback.print_stack()
    return 0


_error_handler_ptr = xlib.XErrorHandler(_error_handler)
xlib.XSetErrorHandler(_error_handler_ptr)


class XlibDisplay(XlibSelectDevice, Display):
    _display = None  # POINTER(xlib.Display)

    _x_im = None  # X input method
    # TODO close _x_im when display connection closed.
    _enable_xsync = False
    _screens: list[XlibScreen | XlibScreenXrandr | XlibScreenXinerama]

    def __init__(self, name=None, x_screen=None):
        self._screens = []

        if x_screen is None:
            x_screen = 0

        if isinstance(name, str):
            name = c_char_p(name.encode('ascii'))

        self._display = xlib.XOpenDisplay(name)
        if not self._display:
            raise NoSuchDisplayException(f'Cannot connect to "{name}"')

        screen_count = xlib.XScreenCount(self._display)
        if x_screen >= screen_count:
            raise NoSuchDisplayException(f'Display "{name}" has no screen {x_screen:d}')

        super().__init__()
        self.name = name
        self.x_screen = x_screen

        self._fileno = xlib.XConnectionNumber(self._display)
        self._window_map = {}

        # Initialise XSync
        if _have_xsync:
            event_base = c_int()
            error_base = c_int()
            if xsync.XSyncQueryExtension(self._display, byref(event_base), byref(error_base)):
                major_version = c_int()
                minor_version = c_int()
                if xsync.XSyncInitialize(self._display, byref(major_version), byref(minor_version)):
                    self._enable_xsync = True

        # Add to event loop select list.  Assume we never go away.
        app.platform_event_loop.select_devices.add(self)

    def get_default_screen(self) -> Screen:
        screens = self.get_screens()
        if _have_xrandr:
            for screen in screens:
                if screen.is_primary:
                    return screen

        # Couldn't find a default screen, use the first in the list.
        return self._screens[0]

    def get_screens(self) -> list[XlibScreen]:
        self._screens = []

        # Use XRandr if available, as it appears more maintained and widely supported.
        if _have_xrandr:
            root = xlib.XDefaultRootWindow(self._display)

            res_ptr = xrandr.XRRGetScreenResources(self._display, root)
            if res_ptr:
                primary = xrandr.XRRGetOutputPrimary(self._display, root)

                res = res_ptr.contents
                for i in range(res.noutput):
                    output_id = res.outputs[i]
                    output_info_ptr = xrandr.XRRGetOutputInfo(self._display, res_ptr, output_id)
                    if not output_info_ptr:
                        xrandr.XRRFreeOutputInfo(output_info_ptr)
                        continue

                    output_info: xrandr.XRROutputInfo = output_info_ptr.contents

                    crtc_info_ptr = xrandr.XRRGetCrtcInfo(self._display, res_ptr, output_info.crtc)
                    if not crtc_info_ptr:
                        xrandr.XRRFreeCrtcInfo(crtc_info_ptr)
                        continue

                    crtc_info: xrandr.XRRCrtcInfo = crtc_info_ptr.contents

                    self._screens.append(
                        XlibScreenXrandr(
                            self,
                            crtc_info.x,
                            crtc_info.y,
                            crtc_info.width,
                            crtc_info.height,
                            output_info.crtc,
                            output_id,
                            ctypes.string_at(output_info.name, output_info.nameLen).decode(),
                            output_id == primary,
                        ),
                    )
                    xrandr.XRRFreeCrtcInfo(crtc_info_ptr)
                    xrandr.XRRFreeOutputInfo(output_info_ptr)

            xrandr.XRRFreeScreenResources(res_ptr)

        if not self._screens and _have_xinerama and xinerama.XineramaIsActive(self._display):
            number = c_int()
            infos = xinerama.XineramaQueryScreens(self._display, byref(number))
            infos = cast(infos, POINTER(xinerama.XineramaScreenInfo * number.value)).contents

            using_xinerama = number.value > 1
            for idx, info in enumerate(infos):
                self._screens.append(
                    XlibScreenXinerama(self, info.x_org, info.y_org, info.width, info.height, using_xinerama, idx),
                )
            xlib.XFree(infos)
        elif not self._screens:
            # No xinerama
            screen_info = xlib.XScreenOfDisplay(self._display, self.x_screen)
            screen = XlibScreen(self, 0, 0, screen_info.contents.width, screen_info.contents.height)
            self._screens = [screen]
        return self._screens

    # XlibSelectDevice interface

    def fileno(self) -> int:
        return self._fileno

    def select(self) -> None:
        e = xlib.XEvent()
        while xlib.XPending(self._display):
            xlib.XNextEvent(self._display, e)

            # Key events are filtered by the xlib window event
            # handler so they get a shot at the prefiltered event.
            if e.xany.type not in (xlib.KeyPress, xlib.KeyRelease):
                if xlib.XFilterEvent(e, e.xany.window):
                    continue
            try:
                dispatch = self._window_map[e.xany.window]
            except KeyError:
                continue

            dispatch(e)

    def poll(self) -> int:
        return xlib.XPending(self._display)


class XlibScreen(Screen):
    _initial_mode = None

    def __init__(self, display: XlibDisplay, x: int, y: int, width: int, height: int):
        super().__init__(display, x, y, width, height)

    def get_dpi(self) -> int:
        resource = xlib.XResourceManagerString(self.display._display)
        dpi = 96
        if resource:
            xlib.XrmInitialize()

            db = xlib.XrmGetStringDatabase(resource)
            if db:
                rs_type = c_char_p()
                value = xlib.XrmValue()
                if xlib.XrmGetResource(db, asbytes("Xft.dpi"), asbytes("Xft.dpi"), byref(rs_type), byref(value)):
                    if value.addr and rs_type.value == b'String':
                        dpi = int(value.addr)

                xlib.XrmDestroyDatabase(db)

        return dpi

    def get_scale(self) -> float:
        return self.get_dpi() / 96

    def get_matching_configs(self, template: Config):
        canvas = XlibCanvas(self.display, None)
        configs = template.match(canvas)
        # XXX deprecate
        for config in configs:
            config.screen = self
        return configs

    def get_modes(self) -> list[XlibScreenModeXF86]:
        if not _have_xf86vmode:
            return []

        count = ctypes.c_int()
        info_array = ctypes.POINTER(ctypes.POINTER(xf86vmode.XF86VidModeModeInfo))()
        xf86vmode.XF86VidModeGetAllModeLines(self.display._display, self.display.x_screen, count, info_array)

        depth = xlib.XDefaultDepth(self.display._display, self.display.x_screen)

        # Copy modes out of list and free list
        modes = []
        for i in range(count.value):
            info = xf86vmode.XF86VidModeModeInfo()
            ctypes.memmove(
                ctypes.byref(info),
                ctypes.byref(info_array.contents[i]),
                ctypes.sizeof(info),
            )

            modes.append(XlibScreenModeXF86(self, info, depth))
            if info.privsize:
                xlib.XFree(info.private)
        xlib.XFree(info_array)

        return modes

    def get_mode(self) -> XlibScreenMode:
        modes = self.get_modes()
        if modes:
            return modes[0]
        return None

    def set_mode(self, mode: XlibScreenModeXF86):
        assert mode.screen is self

        if not self._initial_mode:
            self._initial_mode = self.get_mode()
            xlib_vidmoderestore.set_initial_mode(self._initial_mode)

        xf86vmode.XF86VidModeSwitchToMode(self.display._display, self.display.x_screen, mode.info)
        xlib.XFlush(self.display._display)
        xf86vmode.XF86VidModeSetViewPort(self.display._display, self.display.x_screen, 0, 0)
        xlib.XFlush(self.display._display)

        self.width = mode.width
        self.height = mode.height

    def restore_mode(self):
        if self._initial_mode:
            self.set_mode(self._initial_mode)

    def get_display_id(self) -> int:
        # No real unique ID is available, just hash together the properties.
        return hash((self.x, self.y, self.width, self.height))

    def get_monitor_name(self) -> str:
        # No way to get any screen name without XRandr or EDID information.
        return "Unknown"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(display={self.display!r}, x={self.x}, y={self.y}, "
            f"width={self.width}, height={self.height})"
        )


class XlibScreenXinerama(XlibScreen):
    def __init__(self, display: XlibDisplay, x: int, y: int, width: int, height: int, using_xinerama: bool, idx: int) -> None:
        super().__init__(display, x, y, width, height)
        self._xinerama = using_xinerama
        self.idx = idx

    def get_display_id(self) -> int:
        # No real unique ID is available, just hash together the properties.
        return hash((self.idx, self.x, self.y, self.width, self.height))

    def get_modes(self):
        if self._xinerama:
            # If Xinerama/TwinView is enabled, xf86vidmode's modelines
            # correspond to metamodes, which don't distinguish one screen from
            # another.  XRandR (broken) or NV (complicated) extensions needed.
            return []

        return super().get_modes()


class XlibScreenXrandr(XlibScreen):
    def __init__(
        self,
        display: XlibDisplay,
        x: int,
        y: int,
        width: int,
        height: int,
        crtc_id: int,
        output_id: int,
        name: str,
        is_primary: bool,
    ):
        super().__init__(display, x, y, width, height)
        self.crtc_id = crtc_id
        self.output_id = output_id
        self.name = name
        self._is_primary = is_primary

    @property
    def is_primary(self):
        return self._is_primary

    @staticmethod
    def _get_mode_info(resource: xrandr.XRRScreenResources, rrmode_id: int) -> xrandr.XRRModeInfo | None:
        for i in range(resource.nmode):
            if resource.modes[i].id == rrmode_id:
                return resource.modes[i]

        return None

    def set_mode(self, mode: XlibScreenModeXrandr) -> None:
        assert mode.screen is self

        if not self._initial_mode:
            self._initial_mode = self.get_mode()

        root = xlib.XDefaultRootWindow(self.display._display)
        res_ptr = xrandr.XRRGetScreenResourcesCurrent(self.display._display, root)
        if res_ptr:
            crtc_info_ptr = xrandr.XRRGetCrtcInfo(self.display._display, res_ptr, self.crtc_id)
            if crtc_info_ptr:
                crtc_info = crtc_info_ptr.contents
                status = xrandr.XRRSetCrtcConfig(
                    self.display._display,
                    res_ptr,
                    self.crtc_id,
                    xlib.CurrentTime,
                    crtc_info.x,
                    crtc_info.y,
                    mode.mode_id,
                    crtc_info.rotation,
                    crtc_info.outputs,
                    crtc_info.noutput,
                )
                if status != 0 and pyglet.options['debug_x11']:
                    warnings.warn(f"Could not set screen mode: {status}")
                xlib.XFlush(self.display._display)

                self.width = mode.width
                self.height = mode.height

            xrandr.XRRFreeCrtcInfo(crtc_info_ptr)
        xrandr.XRRFreeScreenResources(res_ptr)

    def get_modes(self) -> list[XlibScreenModeXrandr]:
        modes = []
        root = xlib.XDefaultRootWindow(self.display._display)
        res_ptr = xrandr.XRRGetScreenResourcesCurrent(self.display._display, root)
        output_info_ptr = xrandr.XRRGetOutputInfo(self.display._display, res_ptr, self.output_id)

        res = res_ptr.contents
        output_info = output_info_ptr.contents

        depth = xlib.XDefaultDepth(self.display._display, self.display.x_screen)

        for i in range(output_info_ptr.contents.nmode):
            mode_id = output_info.modes[i]
            xrandr_mode = self._get_mode_info(res, mode_id)
            if xrandr_mode:
                mode = XlibScreenModeXrandr(self, xrandr_mode, mode_id, depth)
                modes.append(mode)

        xrandr.XRRFreeOutputInfo(output_info_ptr)
        xrandr.XRRFreeScreenResources(res_ptr)
        return modes

    def get_mode(self) -> XlibScreenModeXrandr | None:
        # Return the current mode.
        root = xlib.XDefaultRootWindow(self.display._display)
        res_ptr = xrandr.XRRGetScreenResourcesCurrent(self.display._display, root)
        crtc_info_ptr = xrandr.XRRGetCrtcInfo(self.display._display, res_ptr, self.crtc_id)

        crtc_info = crtc_info_ptr.contents
        found_mode = None

        for mode in self.get_modes():
            if crtc_info.mode == mode.mode_id:
                found_mode = mode
                break

        xrandr.XRRFreeCrtcInfo(crtc_info_ptr)
        xrandr.XRRFreeScreenResources(res_ptr)
        return found_mode

    def get_display_id(self) -> int:
        return self.output_id

    def get_monitor_name(self) -> str:
        return self.name


class XlibScreenMode(ScreenMode):
    def __init__(self, screen: XlibScreen, width: int, height: int, rate: int, depth: int):
        super().__init__(screen)
        self.width = width
        self.height = height
        self.rate = rate
        self.depth = depth


class XlibScreenModeXF86(XlibScreenMode):
    def __init__(self, screen: XlibScreen, info: xf86vmode.XF86VidModeModeInfo, depth: int) -> None:
        self.info = info
        width = info.hdisplay
        height = info.vdisplay
        rate = round((info.dotclock * 1000) / (info.htotal * info.vtotal))
        super().__init__(screen, width, height, rate, depth)

    def __repr__(self) -> str:
        return f'XlibScreenMode(width={self.width!r}, height={self.height!r}, depth={self.depth!r}, rate={self.rate})'


class XlibScreenModeXrandr(XlibScreenMode):
    def __init__(self, screen: XlibScreen, mode_info: xrandr.XRRModeInfo, mode_id: int, depth: int) -> None:
        self.mode_id = mode_id
        super().__init__(screen, mode_info.width, mode_info.height, self._calculate_refresh_rate(mode_info), depth)

    @staticmethod
    def _calculate_refresh_rate(mode_info: xrandr.XRRModeInfo) -> int:
        if mode_info.hTotal > 0 and mode_info.vTotal > 0:
            return round(mode_info.dotClock / (mode_info.hTotal * mode_info.vTotal))
        return 0

    def __repr__(self) -> str:
        return f'XlibScreenMode(width={self.width!r}, height={self.height!r}, depth={self.depth!r}, rate={self.rate})'


class XlibCanvas(Canvas):  # noqa: D101
    display: XlibDisplay

    def __init__(self, display: XlibDisplay, x_window: xlib.Window) -> None:  # noqa: D107
        super().__init__(display)
        self.x_window = x_window
