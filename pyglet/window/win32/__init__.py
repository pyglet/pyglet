from __future__ import annotations

import sys
import unicodedata
from ctypes.wintypes import HICON, HWND, MSG, POINT, RECT, UINT
from functools import lru_cache
from typing import Callable, Sequence

from pyglet import compat_platform
from pyglet.libs.win32 import constants
from pyglet.libs.win32.types import (
    BITMAPINFOHEADER,
    HCURSOR,
    HRAWINPUT,
    ICONINFO,
    MINMAXINFO,
    RAWINPUT,
    RAWINPUTHEADER,
    RECT,
    SIZE,
    TRACKMOUSEEVENT,
    WCHAR,
)
from pyglet.libs.win32.winkey import chmap, keymap

if compat_platform not in ('cygwin', 'win32'):
    raise ImportError('Not a win32 platform.')

from ctypes import (
    POINTER,
    byref,
    c_int,
    c_int16,
    c_short,
    c_void_p,
    c_wchar_p,
    cast,
    create_unicode_buffer,
    memmove,
    sizeof,
    wstring_at,
)

import pyglet
from pyglet.display.win32 import Win32Canvas
from pyglet.event import EventDispatcher
from pyglet.libs.win32 import (
    BITMAPV5HEADER,
    DWM_BLURBEHIND,
    MAKEINTRESOURCE,
    RAWINPUTDEVICE,
    WNDCLASS,
    WNDPROC,
    _dwmapi,
    _gdi32,
    _kernel32,
    _shell32,
    _user32,
)
from pyglet.window import (
    BaseWindow,
    DefaultMouseCursor,
    ImageMouseCursor,
    MouseCursor,
    WindowException,
    _PlatformEventHandler,
    _ViewEventHandler,
    key,
    mouse,
)

# symbol,ctrl -> motion mapping
_motion_map: dict[tuple[int, bool], int] = {
    (key.UP, False): key.MOTION_UP,
    (key.RIGHT, False): key.MOTION_RIGHT,
    (key.DOWN, False): key.MOTION_DOWN,
    (key.LEFT, False): key.MOTION_LEFT,
    (key.RIGHT, True): key.MOTION_NEXT_WORD,
    (key.LEFT, True): key.MOTION_PREVIOUS_WORD,
    (key.HOME, False): key.MOTION_BEGINNING_OF_LINE,
    (key.END, False): key.MOTION_END_OF_LINE,
    (key.PAGEUP, False): key.MOTION_PREVIOUS_PAGE,
    (key.PAGEDOWN, False): key.MOTION_NEXT_PAGE,
    (key.HOME, True): key.MOTION_BEGINNING_OF_FILE,
    (key.END, True): key.MOTION_END_OF_FILE,
    (key.BACKSPACE, False): key.MOTION_BACKSPACE,
    (key.DELETE, False): key.MOTION_DELETE,
    (key.C, True): key.MOTION_COPY,
    (key.V, True): key.MOTION_PASTE,
}


class Win32MouseCursor(MouseCursor):
    gl_drawable: bool = False
    hw_drawable: bool = True

    def __init__(self, cursor: HCURSOR) -> None:
        self.cursor = cursor


# This is global state, we have to be careful not to set the same state twice,
# which will throw off the ShowCursor counter.
_win32_cursor_visible: bool = True

Win32EventHandler = _PlatformEventHandler
ViewEventHandler = _ViewEventHandler


class Win32Window(BaseWindow):
    _window_class = None
    _hwnd = None
    _dc = None
    _wgl_context = None
    _tracking = False
    _hidden = False
    _has_focus = False

    _exclusive_keyboard: bool = False
    _exclusive_keyboard_focus: bool = True
    _exclusive_mouse: bool = False
    _exclusive_mouse_focus: bool = True
    _exclusive_mouse_screen = None
    _exclusive_mouse_lpos = None
    _exclusive_mouse_buttons = 0
    _mouse_platform_visible: bool = True
    _pending_click: bool = False
    _in_title_bar: bool = False

    _mouse_scale: float = 1

    _keyboard_state: dict[int, bool] = {0x02A: False, 0x036: False}  # For shift keys.

    _ws_style: int = 0
    _ex_ws_style: int = 0
    _minimum_size: tuple[int, int] | None = None
    _maximum_size: tuple[int, int] | None = None

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        # Bind event handlers
        self._event_handlers: dict[int, Callable] = {}
        self._view_event_handlers: dict[int, Callable] = {}
        for func_name in self._platform_event_names:
            if not hasattr(self, func_name):
                continue
            func = getattr(self, func_name)
            for message in func._platform_event_data:  # noqa: SLF001
                if hasattr(func, '_view'):
                    self._view_event_handlers[message] = func
                else:
                    self._event_handlers[message] = func

        self._always_dwm = sys.getwindowsversion() >= (6, 2)
        self._interval = 0

        super().__init__(*args, **kwargs)

    def _recreate(self, changes: Sequence[str]) -> None:
        if 'context' in changes:
            self._wgl_context = None

        self._create()

    def _create(self) -> None:
        # Ensure style is set before determining width/height.
        if self._fullscreen:
            self._ws_style = constants.WS_POPUP
            self._ex_ws_style = 0  # WS_EX_TOPMOST
        else:
            styles = {
                self.WINDOW_STYLE_DEFAULT: (constants.WS_OVERLAPPEDWINDOW, 0),
                self.WINDOW_STYLE_DIALOG: (constants.WS_OVERLAPPED | constants.WS_CAPTION | constants.WS_SYSMENU,
                                           constants.WS_EX_DLGMODALFRAME),
                self.WINDOW_STYLE_TOOL: (constants.WS_OVERLAPPED | constants.WS_CAPTION | constants.WS_SYSMENU,
                                         constants.WS_EX_TOOLWINDOW),
                self.WINDOW_STYLE_BORDERLESS: (constants.WS_POPUP, 0),
                self.WINDOW_STYLE_TRANSPARENT: (constants.WS_OVERLAPPEDWINDOW,
                                                constants.WS_EX_LAYERED),
                self.WINDOW_STYLE_OVERLAY: (constants.WS_POPUP,
                                            constants.WS_EX_LAYERED | constants.WS_EX_TRANSPARENT),
            }
            self._ws_style, self._ex_ws_style = styles[self._style]

        if self._resizable and not self._fullscreen:
            self._ws_style |= constants.WS_THICKFRAME
        else:
            self._ws_style &= ~(constants.WS_THICKFRAME | constants.WS_MAXIMIZEBOX)

        self._dpi = self._screen.get_dpi()

        if self._fullscreen:
            width = self.screen.width
            height = self.screen.height
        else:
            if pyglet.options.dpi_scaling in ("scaled", "stretch"):
                w, h = self.get_requested_size()
                self._width = int(w * self.scale)
                self._height = int(h * self.scale)

                if pyglet.options.dpi_scaling == "stretch":
                    self._mouse_scale = self.scale

            width, height = \
                self._client_to_window_size(self._width, self._height, self._dpi)

        if not self._window_class:
            module = _kernel32.GetModuleHandleW(None)
            white = _gdi32.GetStockObject(constants.WHITE_BRUSH)
            black = _gdi32.GetStockObject(constants.BLACK_BRUSH)
            self._window_class = WNDCLASS()
            self._window_class.lpszClassName = 'GenericAppClass%d' % id(self)
            self._window_class.lpfnWndProc = WNDPROC(
                self._get_window_proc(self._event_handlers))
            self._window_class.style = constants.CS_VREDRAW | constants.CS_HREDRAW | constants.CS_OWNDC
            self._window_class.hInstance = 0
            self._window_class.hIcon = _user32.LoadImageW(module, MAKEINTRESOURCE(1), constants.IMAGE_ICON,
                                                          0, 0, constants.LR_DEFAULTSIZE | constants.LR_SHARED)
            self._window_class.hbrBackground = black
            self._window_class.lpszMenuName = None
            self._window_class.cbClsExtra = 0
            self._window_class.cbWndExtra = 0
            _user32.RegisterClassW(byref(self._window_class))

            self._view_window_class = WNDCLASS()
            self._view_window_class.lpszClassName = \
                'GenericViewClass%d' % id(self)
            self._view_window_class.lpfnWndProc = WNDPROC(
                self._get_window_proc(self._view_event_handlers))
            self._view_window_class.style = 0
            self._view_window_class.hInstance = 0
            self._view_window_class.hIcon = 0
            self._view_window_class.hbrBackground = white
            self._view_window_class.lpszMenuName = None
            self._view_window_class.cbClsExtra = 0
            self._view_window_class.cbWndExtra = 0
            _user32.RegisterClassW(byref(self._view_window_class))

        if not self._hwnd:
            self._hwnd = _user32.CreateWindowExW(
                self._ex_ws_style,
                self._window_class.lpszClassName,
                '',
                self._ws_style,
                constants.CW_USEDEFAULT,
                constants.CW_USEDEFAULT,
                width,
                height,
                0,
                0,
                self._window_class.hInstance,
                0)

            # View Hwnd is for the client area so certain events (mouse events) don't trigger outside of area.
            self._view_hwnd = _user32.CreateWindowExW(
                0,
                self._view_window_class.lpszClassName,
                '',
                constants.WS_CHILD | constants.WS_VISIBLE,
                0, 0, 0, 0,
                self._hwnd,
                0,
                self._view_window_class.hInstance,
                0)

            self._dc = _user32.GetDC(self._view_hwnd)

            # Only allow files being dropped if specified.
            if self._file_drops:
                # Allows UAC to not block the drop files request if low permissions. All 3 must be set.
                if constants.WINDOWS_7_OR_GREATER:
                    _user32.ChangeWindowMessageFilterEx(self._hwnd, constants.WM_DROPFILES, constants.MSGFLT_ALLOW,
                                                        None)
                    _user32.ChangeWindowMessageFilterEx(self._hwnd, constants.WM_COPYDATA, constants.MSGFLT_ALLOW, None)
                    _user32.ChangeWindowMessageFilterEx(self._hwnd, constants.WM_COPYGLOBALDATA, constants.MSGFLT_ALLOW,
                                                        None)

                _shell32.DragAcceptFiles(self._hwnd, True)

            # Set the raw keyboard to handle shift state. This is required as legacy events cannot handle shift states
            # when both keys are used together. View Hwnd as none changes focus to follow keyboard.
            raw_keyboard = RAWINPUTDEVICE(0x01, 0x06, 0, None)
            if not _user32.RegisterRawInputDevices(
                    byref(raw_keyboard), 1, sizeof(RAWINPUTDEVICE)):
                print('Warning: Failed to unregister raw input keyboard.')
        else:
            # Window already exists, update it with new style

            # We need to hide window here, otherwise Windows forgets
            # to redraw the whole screen after leaving fullscreen.
            _user32.ShowWindow(self._hwnd, constants.SW_HIDE)

            _user32.SetWindowLongW(self._hwnd,
                                   constants.GWL_STYLE,
                                   self._ws_style)
            _user32.SetWindowLongW(self._hwnd,
                                   constants.GWL_EXSTYLE,
                                   self._ex_ws_style)

        # Position and size window
        if self._fullscreen:
            hwnd_after = constants.HWND_TOPMOST if self.style == 'overlay' else constants.HWND_NOTOPMOST
            _user32.SetWindowPos(self._hwnd, hwnd_after,
                                 self._screen.x, self._screen.y, width, height, constants.SWP_FRAMECHANGED)
        elif self.style == 'transparent' or self.style == 'overlay':
            _user32.SetLayeredWindowAttributes(self._hwnd, 0, 254, constants.LWA_ALPHA)
            if self.style == 'overlay':
                _user32.SetWindowPos(self._hwnd, constants.HWND_TOPMOST, 0,
                                     0, width, height, constants.SWP_NOMOVE | constants.SWP_NOSIZE)
        else:
            _user32.SetWindowPos(self._hwnd, constants.HWND_NOTOPMOST,
                                 0, 0, width, height, constants.SWP_NOMOVE | constants.SWP_FRAMECHANGED)

        self._update_view_location(self._width, self._height)

        # Context must be created after window is created.
        if not self._wgl_context:
            self.canvas = Win32Canvas(self.display, self._view_hwnd, self._dc)
            self.context.attach(self.canvas)
            self._wgl_context = self.context._context  # noqa: SLF001

        self.switch_to()

        self.set_caption(self._caption)
        self.set_vsync(self._vsync)

        if self._visible:
            self.set_visible()
            # Might need resize event if going from fullscreen to fullscreen
            self.dispatch_event('_on_internal_resize', self._width, self._height)
            self.dispatch_event('on_expose')

    def _update_view_location(self, width: int, height: int) -> None:
        if self._fullscreen:
            x = (self.screen.width - width) // 2
            y = (self.screen.height - height) // 2
        else:
            x = y = 0
        _user32.SetWindowPos(self._view_hwnd, 0,
                             x, y, width, height, constants.SWP_NOZORDER | constants.SWP_NOOWNERZORDER)

    def close(self) -> None:
        if not self._hwnd:
            super().close()
            return

        self.set_mouse_platform_visible(True)

        _user32.DestroyWindow(self._hwnd)
        _user32.UnregisterClassW(self._view_window_class.lpszClassName, 0)
        _user32.UnregisterClassW(self._window_class.lpszClassName, 0)

        self._window_class = None
        self._view_window_class = None
        self._view_event_handlers.clear()
        self._event_handlers.clear()
        self._hwnd = None
        self._dc = None
        self._wgl_context = None
        super().close()

    def _dwm_composition_enabled(self) -> int:
        """ Checks if Windows DWM is enabled (Windows Vista+)
            Note: Always on for Windows 8+
        """
        is_enabled = c_int()
        _dwmapi.DwmIsCompositionEnabled(byref(is_enabled))
        return is_enabled.value

    @property
    def vsync(self) -> bool:
        return bool(self._interval)

    def set_vsync(self, vsync: bool) -> None:
        if pyglet.options['vsync'] is not None:
            vsync = pyglet.options['vsync']

        self._interval = vsync

        # Disable interval if composition is enabled to avoid conflict with DWM.
        if not self._fullscreen and (self._always_dwm or self._dwm_composition_enabled()):
            vsync = 0

        self.context.set_vsync(vsync)

    def switch_to(self) -> None:
        self.context.set_current()

    def update_transparency(self) -> None:
        region = _gdi32.CreateRectRgn(0, 0, -1, -1)
        bb = DWM_BLURBEHIND()
        bb.dwFlags = constants.DWM_BB_ENABLE | constants.DWM_BB_BLURREGION
        bb.hRgnBlur = region
        bb.fEnable = True

        _dwmapi.DwmEnableBlurBehindWindow(self._hwnd, byref(bb))
        _gdi32.DeleteObject(region)

    def flip(self) -> None:
        self.draw_mouse_cursor()

        if not self._fullscreen and (self._always_dwm or self._dwm_composition_enabled()) and self._interval:
            _dwmapi.DwmFlush()

        if self.style in ('overlay', 'transparent'):
            self.update_transparency()

        self.context.flip()

    def set_location(self, x: int, y: int) -> None:
        x, y = self._client_to_window_pos(x, y)
        _user32.SetWindowPos(self._hwnd, 0, x, y, 0, 0,
                             (constants.SWP_NOZORDER |
                              constants.SWP_NOSIZE |
                              constants.SWP_NOOWNERZORDER))

    def get_location(self) -> tuple[int, int]:
        point = POINT(0, 0)
        _user32.ClientToScreen(self._hwnd, byref(point))
        return point.x, point.y

    def set_size(self, width: int, height: int) -> None:
        if pyglet.options.dpi_scaling in ("scaled", "stretch"):
            width = int(width * self.scale)
            height = int(height * self.scale)

        super().set_size(width, height)
        width, height = self._client_to_window_size_dpi(width, height)
        _user32.SetWindowPos(self._hwnd, 0, 0, 0, width, height,
                             (constants.SWP_NOZORDER | constants.SWP_NOMOVE | constants.SWP_NOOWNERZORDER))
        self.dispatch_event('_on_internal_resize', self._width, self._height)

    def set_minimum_size(self, width: int, height: int) -> None:
        self._minimum_size = width, height

    def set_maximum_size(self, width: int, height: int) -> None:
        self._maximum_size = width, height

    def activate(self) -> None:
        _user32.SetForegroundWindow(self._hwnd)

    def set_visible(self, visible: bool = True) -> None:
        if visible:
            insertAfter = constants.HWND_TOP
            _user32.SetWindowPos(self._hwnd, insertAfter, 0, 0, 0, 0,
                                 constants.SWP_NOMOVE | constants.SWP_NOSIZE | constants.SWP_SHOWWINDOW)
            self.dispatch_event('_on_internal_resize', self._width, self._height)
            self.activate()
            self.dispatch_event('on_show')
        else:
            _user32.ShowWindow(self._hwnd, constants.SW_HIDE)
            self.dispatch_event('on_hide')
        self._visible = visible
        self.set_mouse_platform_visible()

    def minimize(self) -> None:
        _user32.ShowWindow(self._hwnd, constants.SW_MINIMIZE)

    def maximize(self) -> None:
        _user32.ShowWindow(self._hwnd, constants.SW_MAXIMIZE)

    def get_window_screen(self):
        """ Gets the current screen the window is on.
            If between monitors will retrieve the screen with the most screen space.
        """
        handle = _user32.MonitorFromWindow(self._hwnd, constants.MONITOR_DEFAULTTONEAREST)
        return [screen for screen in self.display.get_screens() if screen._handle == handle][0]

    def set_caption(self, caption: str) -> None:
        self._caption = caption
        _user32.SetWindowTextW(self._hwnd, c_wchar_p(caption))

    def set_mouse_platform_visible(self, platform_visible: bool | None = None) -> None:
        if platform_visible is None:
            platform_visible = (self._mouse_visible and
                                not self._exclusive_mouse and
                                (not self._mouse_cursor.gl_drawable or self._mouse_cursor.hw_drawable)) or \
                               (not self._mouse_in_window or
                                not self._has_focus)

        if platform_visible and self._mouse_cursor.hw_drawable:
            if isinstance(self._mouse_cursor, Win32MouseCursor):
                cursor = self._mouse_cursor.cursor
            elif isinstance(self._mouse_cursor, DefaultMouseCursor):
                cursor = _user32.LoadCursorW(None, MAKEINTRESOURCE(constants.IDC_ARROW))
            else:
                cursor = self._create_cursor_from_image(self._mouse_cursor)

            _user32.SetClassLongPtrW(self._view_hwnd, constants.GCL_HCURSOR, cursor)
            _user32.SetCursor(cursor)

        if platform_visible == self._mouse_platform_visible:
            return

        self._set_cursor_visibility(platform_visible)

        self._mouse_platform_visible = platform_visible

    def get_size(self) -> tuple[int, int]:
        if pyglet.options.dpi_scaling == "stretch":
            return int(self._width / self.scale), int(self._height / self.scale)

        return self._width, self._height

    def get_framebuffer_size(self) -> tuple[int, int]:
        return self._width, self._height

    def _set_cursor_visibility(self, platform_visible: bool) -> None:
        # Avoid calling ShowCursor with the current visibility (which would
        # push the counter too far away from zero).
        global _win32_cursor_visible  # noqa: PLW0603
        if _win32_cursor_visible != platform_visible:
            _user32.ShowCursor(platform_visible)
            _win32_cursor_visible = platform_visible

    def _update_clipped_cursor(self) -> None:
        # Clip to client area, to prevent large mouse movements taking
        # it outside the client area.
        if self._in_title_bar or self._pending_click:
            return

        rect = RECT()
        _user32.GetClientRect(self._view_hwnd, byref(rect))
        _user32.MapWindowPoints(self._view_hwnd, constants.HWND_DESKTOP,
                                byref(rect), 2)

        # For some reason borders can be off 1 pixel, allowing cursor into frame/minimize/exit buttons?
        rect.top += 1
        rect.left += 1
        rect.right -= 1
        rect.bottom -= 1

        _user32.ClipCursor(byref(rect))

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        if self._exclusive_mouse == exclusive and \
                self._exclusive_mouse_focus == self._has_focus:
            return

        # Mouse: UsagePage = 1, Usage = 2
        raw_mouse = RAWINPUTDEVICE(0x01, 0x02, 0, None)
        if not exclusive:
            raw_mouse.dwFlags = constants.RIDEV_REMOVE
            raw_mouse.hwndTarget = None

        if not _user32.RegisterRawInputDevices(  # noqa: SIM102
                byref(raw_mouse), 1, sizeof(RAWINPUTDEVICE)):
            if exclusive:
                msg = 'Cannot enter mouse exclusive mode.'
                raise WindowException(msg)

        self._exclusive_mouse_buttons = 0
        if exclusive and self._has_focus:
            self._update_clipped_cursor()
        else:
            # Release clip
            _user32.ClipCursor(None)

        self._exclusive_mouse = exclusive
        self._exclusive_mouse_focus = self._has_focus
        self.set_mouse_platform_visible(not exclusive)

    def set_mouse_position(self, x: int, y: int, absolute: bool = False) -> None:
        if not absolute:
            rect = RECT()
            _user32.GetClientRect(self._view_hwnd, byref(rect))
            _user32.MapWindowPoints(self._view_hwnd, constants.HWND_DESKTOP, byref(rect), 2)

            x = x + rect.left
            y = rect.top + (rect.bottom - rect.top) - y

        _user32.SetCursorPos(x, y)

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        if self._exclusive_keyboard == exclusive and \
                self._exclusive_keyboard_focus == self._has_focus:
            return

        if exclusive and self._has_focus:
            _user32.RegisterHotKey(self._hwnd, 0, constants.WIN32_MOD_ALT, constants.VK_TAB)
        elif self._exclusive_keyboard and not exclusive:
            _user32.UnregisterHotKey(self._hwnd, 0)

        self._exclusive_keyboard = exclusive
        self._exclusive_keyboard_focus = self._has_focus

    def get_system_mouse_cursor(self, name: str) -> DefaultMouseCursor | Win32MouseCursor:
        if name == self.CURSOR_DEFAULT:
            return DefaultMouseCursor()

        names = {
            self.CURSOR_CROSSHAIR: constants.IDC_CROSS,
            self.CURSOR_HAND: constants.IDC_HAND,
            self.CURSOR_HELP: constants.IDC_HELP,
            self.CURSOR_NO: constants.IDC_NO,
            self.CURSOR_SIZE: constants.IDC_SIZEALL,
            self.CURSOR_SIZE_UP: constants.IDC_SIZENS,
            self.CURSOR_SIZE_UP_RIGHT: constants.IDC_SIZENESW,
            self.CURSOR_SIZE_RIGHT: constants.IDC_SIZEWE,
            self.CURSOR_SIZE_DOWN_RIGHT: constants.IDC_SIZENWSE,
            self.CURSOR_SIZE_DOWN: constants.IDC_SIZENS,
            self.CURSOR_SIZE_DOWN_LEFT: constants.IDC_SIZENESW,
            self.CURSOR_SIZE_LEFT: constants.IDC_SIZEWE,
            self.CURSOR_SIZE_UP_LEFT: constants.IDC_SIZENWSE,
            self.CURSOR_SIZE_UP_DOWN: constants.IDC_SIZENS,
            self.CURSOR_SIZE_LEFT_RIGHT: constants.IDC_SIZEWE,
            self.CURSOR_TEXT: constants.IDC_IBEAM,
            self.CURSOR_WAIT: constants.IDC_WAIT,
            self.CURSOR_WAIT_ARROW: constants.IDC_APPSTARTING,
        }
        if name not in names:
            msg = f'Unknown cursor name "{name}"'
            raise RuntimeError(msg)
        cursor = _user32.LoadCursorW(None, MAKEINTRESOURCE(names[name]))
        return Win32MouseCursor(cursor)

    def set_icon(self, *images: pyglet.image.ImageData) -> None:
        # XXX Undocumented AFAICT, but XP seems happy to resize an image
        # of any size, so no scaling necessary.

        def best_image(width: int, height: int) -> pyglet.image.ImageData:
            # A heuristic for finding the closest sized image to required size.
            b_image = images[0]
            for img in images:
                if img.width == width and img.height == height:
                    # Exact match always used
                    return img
                if img.width >= width and \
                        img.width * img.height > b_image.width * b_image.height:
                    # At least wide enough, and largest area
                    b_image = img
            return b_image

        def get_icon(img: pyglet.image.ImageData) -> HICON:
            # Alpha-blended icon: see http://support.microsoft.com/kb/318876
            fmt = 'BGRA'
            pitch = len(fmt) * img.width

            header = BITMAPV5HEADER()
            header.bV5Size = sizeof(header)
            header.bV5Width = img.width
            header.bV5Height = img.height
            header.bV5Planes = 1
            header.bV5BitCount = 32
            header.bV5Compression = constants.BI_BITFIELDS
            header.bV5RedMask = 0x00ff0000
            header.bV5GreenMask = 0x0000ff00
            header.bV5BlueMask = 0x000000ff
            header.bV5AlphaMask = 0xff000000

            hdc = _user32.GetDC(None)
            dataptr = c_void_p()
            bitmap = _gdi32.CreateDIBSection(hdc, byref(header), constants.DIB_RGB_COLORS,
                                             byref(dataptr), None, 0)
            _user32.ReleaseDC(None, hdc)

            img = img.get_image_data()
            data = img.get_data(fmt, pitch)
            memmove(dataptr, data, len(data))

            mask = _gdi32.CreateBitmap(img.width, img.height, 1, 1, None)

            iconinfo = ICONINFO()
            iconinfo.fIcon = True
            iconinfo.hbmMask = mask
            iconinfo.hbmColor = bitmap
            icon_indirect = _user32.CreateIconIndirect(byref(iconinfo))

            _gdi32.DeleteObject(mask)
            _gdi32.DeleteObject(bitmap)

            return icon_indirect

        # Set large icon
        image = best_image(_user32.GetSystemMetrics(constants.SM_CXICON),
                           _user32.GetSystemMetrics(constants.SM_CYICON))
        icon = get_icon(image)
        _user32.SetClassLongPtrW(self._hwnd, constants.GCL_HICON, icon)

        # Set small icon
        image = best_image(_user32.GetSystemMetrics(constants.SM_CXSMICON),
                           _user32.GetSystemMetrics(constants.SM_CYSMICON))
        icon = get_icon(image)
        _user32.SetClassLongPtrW(self._hwnd, constants.GCL_HICONSM, icon)

    @lru_cache  # noqa: B019
    def _create_cursor_from_image(self, cursor: ImageMouseCursor) -> HICON:
        """Creates platform cursor from an ImageCursor instance."""
        fmt = 'BGRA'
        image = cursor.texture
        pitch = len(fmt) * image.width

        header = BITMAPINFOHEADER()
        header.biSize = sizeof(header)
        header.biWidth = image.width
        header.biHeight = image.height
        header.biPlanes = 1
        header.biBitCount = 32

        hdc = _user32.GetDC(None)
        dataptr = c_void_p()
        bitmap = _gdi32.CreateDIBSection(hdc, byref(header), constants.DIB_RGB_COLORS,
                                         byref(dataptr), None, 0)
        _user32.ReleaseDC(None, hdc)

        image = image.get_image_data()
        data = image.get_data(fmt, pitch)
        memmove(dataptr, data, len(data))

        mask = _gdi32.CreateBitmap(image.width, image.height, 1, 1, None)

        iconinfo = ICONINFO()
        iconinfo.fIcon = False
        iconinfo.hbmMask = mask
        iconinfo.hbmColor = bitmap
        iconinfo.xHotspot = int(cursor.hot_x)
        iconinfo.yHotspot = int(image.height - cursor.hot_y)
        icon = _user32.CreateIconIndirect(byref(iconinfo))

        _gdi32.DeleteObject(mask)
        _gdi32.DeleteObject(bitmap)

        return icon

    def set_clipboard_text(self, text: str) -> None:
        valid = _user32.OpenClipboard(self._view_hwnd)
        if not valid:
            return

        _user32.EmptyClipboard()

        size = (len(text) + 1) * sizeof(WCHAR)  # UTF-16

        cb_data = _kernel32.GlobalAlloc(constants.GMEM_MOVEABLE, size)
        locked_data = _kernel32.GlobalLock(cb_data)
        memmove(locked_data, text, size)  # Trying to encode in utf-16 causes garbled text. Accepts str fine?
        _kernel32.GlobalUnlock(cb_data)

        _user32.SetClipboardData(constants.CF_UNICODETEXT, cb_data)

        _user32.CloseClipboard()

    def get_clipboard_text(self) -> str:
        text = ''

        valid = _user32.OpenClipboard(self._view_hwnd)
        if not valid:
            print('Could not open clipboard')
            return ''

        cb_obj = _user32.GetClipboardData(constants.CF_UNICODETEXT)
        if cb_obj:
            locked_data = _kernel32.GlobalLock(cb_obj)
            if locked_data:
                text = wstring_at(locked_data)

                _kernel32.GlobalUnlock(cb_obj)

        _user32.CloseClipboard()
        return text

    # Private util
    def _client_to_window_size(self, width: int, height: int, dpi: int) -> tuple[int, int]:
        rect = RECT()
        rect.left = 0
        rect.top = 0
        rect.right = width
        rect.bottom = height

        if constants.WINDOWS_10_ANNIVERSARY_UPDATE_OR_GREATER:
            _user32.AdjustWindowRectExForDpi(byref(rect),
                                             self._ws_style, False, self._ex_ws_style, dpi)
        else:
            _user32.AdjustWindowRectEx(byref(rect),
                                       self._ws_style, False, self._ex_ws_style)

        return rect.right - rect.left, rect.bottom - rect.top

    def _client_to_window_size_dpi(self, width, height):
        """ This returns the true window size factoring in styles, borders, title bars.
            Retrieves DPI directly from the Window hwnd, used after window creation.
        """
        rect = RECT()
        rect.left = 0
        rect.top = 0
        rect.right = width
        rect.bottom = height

        if constants.WINDOWS_10_ANNIVERSARY_UPDATE_OR_GREATER:
            _user32.AdjustWindowRectExForDpi(byref(rect),
                self._ws_style, False, self._ex_ws_style, _user32.GetDpiForWindow(self._hwnd))
        else:
            _user32.AdjustWindowRectEx(byref(rect),
                self._ws_style, False, self._ex_ws_style)

        return rect.right - rect.left, rect.bottom - rect.top

    def _client_to_window_pos(self, x: int, y: int) -> tuple[int, int]:
        rect = RECT(x, y, x, y)

        if constants.WINDOWS_10_ANNIVERSARY_UPDATE_OR_GREATER:
            _user32.AdjustWindowRectExForDpi(byref(rect),
                self._ws_style, False, self._ex_ws_style, _user32.GetDpiForWindow(self._hwnd))
        else:
            _user32.AdjustWindowRectEx(byref(rect),
                self._ws_style, False, self._ex_ws_style)
        return rect.left, rect.top

    # Event dispatching

    def dispatch_events(self) -> None:
        """Legacy or manual dispatch."""
        from pyglet import app
        app.platform_event_loop.start()
        self._allow_dispatch_event = True
        self.dispatch_pending_events()

        msg = MSG()
        while _user32.PeekMessageW(byref(msg), 0, 0, 0, constants.PM_REMOVE):
            _user32.TranslateMessage(byref(msg))
            _user32.DispatchMessageW(byref(msg))
        self._allow_dispatch_event = False

    def dispatch_pending_events(self) -> None:
        """Legacy or manual dispatch."""
        while self._event_queue:
            event = self._event_queue.pop(0)
            if isinstance(event[0], str):
                # pyglet event
                EventDispatcher.dispatch_event(self, *event)
            else:
                # win32 event
                event[0](*event[1:])

    def _get_window_proc(self, event_handlers: dict) -> Callable[[HWND, MSG, int, int], int | None]:
        def f(hwnd: HWND, msg: MSG, wParam: int, lParam: int) -> int | None:
            event_handler = event_handlers.get(msg)
            result = None
            if event_handler:
                if self._allow_dispatch_event or not self._enable_event_queue:
                    result = event_handler(msg, wParam, lParam)
                else:
                    result = 0
                    self._event_queue.append((event_handler, msg,
                                              wParam, lParam))
            if result is None:
                result = _user32.DefWindowProcW(hwnd, msg, wParam, lParam)
            return result

        return f

    # Event handlers

    def _get_modifiers(self, key_lParam: int = 0) -> int:
        modifiers = 0
        if self._keyboard_state[0x036] or self._keyboard_state[0x02A]:
            modifiers |= key.MOD_SHIFT
        if _user32.GetKeyState(constants.VK_CONTROL) & 0xff00:
            modifiers |= key.MOD_CTRL
        if _user32.GetKeyState(constants.VK_LWIN) & 0xff00:
            modifiers |= key.MOD_WINDOWS
        if _user32.GetKeyState(constants.VK_CAPITAL) & 0x00ff:  # toggle
            modifiers |= key.MOD_CAPSLOCK
        if _user32.GetKeyState(constants.VK_NUMLOCK) & 0x00ff:  # toggle
            modifiers |= key.MOD_NUMLOCK
        if _user32.GetKeyState(constants.VK_SCROLL) & 0x00ff:  # toggle
            modifiers |= key.MOD_SCROLLLOCK

        if key_lParam:
            if key_lParam & (1 << 29):
                modifiers |= key.MOD_ALT
        elif _user32.GetKeyState(constants.VK_MENU) < 0:
            modifiers |= key.MOD_ALT
        return modifiers

    @staticmethod
    def _get_location(lParam: int) -> tuple[int, int]:
        x = c_int16(lParam & 0xffff).value
        y = c_int16(lParam >> 16).value
        return x, y

    @Win32EventHandler(constants.WM_KEYDOWN)
    @Win32EventHandler(constants.WM_KEYUP)
    @Win32EventHandler(constants.WM_SYSKEYDOWN)
    @Win32EventHandler(constants.WM_SYSKEYUP)
    def _event_key(self, msg: int, wParam: int, lParam: int) -> int | None:
        repeat = False
        if lParam & (1 << 30):
            if msg not in (constants.WM_KEYUP, constants.WM_SYSKEYUP):
                repeat = True
            ev = 'on_key_release'
        else:
            ev = 'on_key_press'

        symbol = keymap.get(wParam, None)
        if symbol is None:
            ch = _user32.MapVirtualKeyW(wParam, constants.MAPVK_VK_TO_CHAR)
            symbol = chmap.get(ch)

        if symbol is None:
            symbol = key.user_key(wParam)
        elif symbol == key.LCTRL and lParam & (1 << 24):
            symbol = key.RCTRL
        elif symbol == key.LALT and lParam & (1 << 24):
            symbol = key.RALT

        if wParam == constants.VK_SHIFT:
            return None  # Let raw input handle this instead.

        modifiers = self._get_modifiers(lParam)

        if not repeat:
            self.dispatch_event(ev, symbol, modifiers)

        ctrl = modifiers & key.MOD_CTRL != 0
        if (symbol, ctrl) in _motion_map and msg not in (constants.WM_KEYUP, constants.WM_SYSKEYUP):
            motion = _motion_map[symbol, ctrl]
            if modifiers & key.MOD_SHIFT:
                self.dispatch_event('on_text_motion_select', motion)
            else:
                self.dispatch_event('on_text_motion', motion)

        # Send on to DefWindowProc if not exclusive.
        if self._exclusive_keyboard:
            return 0

        return None

    @Win32EventHandler(constants.WM_NCLBUTTONDOWN)
    def _event_ncl_button_down(self, msg: int, wParam: int, lParam: int) -> None:
        self._in_title_bar = True

    @Win32EventHandler(constants.WM_CAPTURECHANGED)
    def _event_capture_changed(self, msg: int, wParam: int, lParam: int) -> None:
        self._in_title_bar = False

        if self._exclusive_mouse:
            state = _user32.GetAsyncKeyState(constants.VK_LBUTTON)
            if not state & 0x8000:  # released
                if self._pending_click:
                    self._pending_click = False

                if self._has_focus or not self._hidden:
                    self._update_clipped_cursor()

    @Win32EventHandler(constants.WM_CHAR)
    def _event_char(self, msg: int, wParam: int, lParam: int) -> int:
        text = chr(wParam)
        if unicodedata.category(text) != 'Cc' or text == '\r':
            self.dispatch_event('on_text', text)
        return 0

    @Win32EventHandler(constants.WM_INPUT)
    def _event_raw_input(self, msg: int, wParam: int, lParam: int) -> int:
        hRawInput = cast(lParam, HRAWINPUT)
        inp = RAWINPUT()
        size = UINT(sizeof(inp))
        _user32.GetRawInputData(hRawInput, constants.RID_INPUT, byref(inp),
                                byref(size), sizeof(RAWINPUTHEADER))

        if inp.header.dwType == constants.RIM_TYPEMOUSE:
            if not self._exclusive_mouse:
                return 0

            rmouse = inp.data.mouse

            if rmouse.usFlags & 0x01 == constants.MOUSE_MOVE_RELATIVE:
                if rmouse.lLastX != 0 or rmouse.lLastY != 0:
                    scale = self.scale
                    # Motion event
                    # In relative motion, Y axis is positive for below.
                    # We invert it for Pyglet so positive is motion up.
                    if self._exclusive_mouse_buttons:
                        self.dispatch_event('on_mouse_drag', 0, 0,
                                            rmouse.lLastX * scale, -rmouse.lLastY * scale,
                                            self._exclusive_mouse_buttons,
                                            self._get_modifiers())
                    else:
                        self.dispatch_event('on_mouse_motion', 0, 0,
                                            rmouse.lLastX, -rmouse.lLastY)
            else:
                if self._exclusive_mouse_lpos is None:
                    self._exclusive_mouse_lpos = rmouse.lLastX, rmouse.lLastY
                last_x, last_y = self._exclusive_mouse_lpos
                rel_x = rmouse.lLastX - last_x
                rel_y = rmouse.lLastY - last_y
                if rel_x != 0 or rel_y != 0.0:
                    # Motion event
                    if self._exclusive_mouse_buttons:
                        self.dispatch_event('on_mouse_drag', 0, 0,
                                            rmouse.lLastX, -rmouse.lLastY,
                                            self._exclusive_mouse_buttons,
                                            self._get_modifiers())
                    else:
                        self.dispatch_event('on_mouse_motion', 0, 0,
                                            rel_x, rel_y)
                    self._exclusive_mouse_lpos = rmouse.lLastX, rmouse.lLastY

        elif inp.header.dwType == constants.RIM_TYPEKEYBOARD:
            if inp.data.keyboard.VKey == 255:
                return 0

            key_up = inp.data.keyboard.Flags & constants.RI_KEY_BREAK

            if inp.data.keyboard.MakeCode == 0x02A:  # LEFT_SHIFT
                if not key_up and not self._keyboard_state[0x02A]:
                    self._keyboard_state[0x02A] = True
                    self.dispatch_event('on_key_press', key.LSHIFT, self._get_modifiers())

                elif key_up and self._keyboard_state[0x02A]:
                    self._keyboard_state[0x02A] = False
                    self.dispatch_event('on_key_release', key.LSHIFT, self._get_modifiers())

            elif inp.data.keyboard.MakeCode == 0x036:  # RIGHT SHIFT
                if not key_up and not self._keyboard_state[0x036]:
                    self._keyboard_state[0x036] = True
                    self.dispatch_event('on_key_press', key.RSHIFT, self._get_modifiers())

                elif key_up and self._keyboard_state[0x036]:
                    self._keyboard_state[0x036] = False
                    self.dispatch_event('on_key_release', key.RSHIFT, self._get_modifiers())

        return 0

    @ViewEventHandler
    @Win32EventHandler(constants.WM_MOUSEMOVE)
    def _event_mousemove(self, msg: int, wParam: int, lParam: int) -> int:
        if self._exclusive_mouse and self._has_focus:
            return 0

        x, y = self._get_location(lParam)
        y = self._height - y

        dx = x - self._mouse_x
        dy = y - self._mouse_y

        if not self._tracking:
            # There is no WM_MOUSEENTER message (!), so fake it from the
            # first WM_MOUSEMOVE event after leaving.  Use self._tracking
            # to determine when to recreate the tracking structure after
            # re-entering (to track the next WM_MOUSELEAVE).
            self._mouse_in_window = True
            self.set_mouse_platform_visible()
            self.dispatch_event('on_mouse_enter', x / self._mouse_scale, y / self._mouse_scale)
            self._tracking = True
            track = TRACKMOUSEEVENT()
            track.cbSize = sizeof(track)
            track.dwFlags = constants.TME_LEAVE
            track.hwndTrack = self._view_hwnd
            _user32.TrackMouseEvent(byref(track))

        # Don't generate motion/drag events when mouse hasn't moved. (Issue
        # 305)
        if self._mouse_x == x and self._mouse_y == y:
            return 0

        self._mouse_x = x
        self._mouse_y = y

        buttons = 0
        if wParam & constants.MK_LBUTTON:
            buttons |= mouse.LEFT
        if wParam & constants.MK_MBUTTON:
            buttons |= mouse.MIDDLE
        if wParam & constants.MK_RBUTTON:
            buttons |= mouse.RIGHT
        if wParam & constants.MK_XBUTTON1:
            buttons |= mouse.MOUSE4
        if wParam & constants.MK_XBUTTON2:
            buttons |= mouse.MOUSE5

        if buttons:
            # Drag event
            modifiers = self._get_modifiers()
            self.dispatch_event('on_mouse_drag',
                                x / self._mouse_scale, y / self._mouse_scale, dx / self._mouse_scale, dy / self._mouse_scale, buttons, modifiers)
        else:
            # Motion event
            self.dispatch_event('on_mouse_motion', x / self._mouse_scale, y / self._mouse_scale, dx * self._mouse_scale, dy * self._mouse_scale)
        return 0

    @ViewEventHandler
    @Win32EventHandler(constants.WM_MOUSELEAVE)
    def _event_mouseleave(self, msg: int, wParam: int, lParam: int) -> int:
        point = POINT()
        _user32.GetCursorPos(byref(point))
        _user32.ScreenToClient(self._view_hwnd, byref(point))
        x = point.x
        y = self._height - point.y
        self._tracking = False
        self._mouse_in_window = False
        self.set_mouse_platform_visible()
        self.dispatch_event('on_mouse_leave', x / self._mouse_scale, y / self._mouse_scale)
        return 0

    def _event_mousebutton(self, ev: str, button: int, lParam: int) -> int:
        if ev == 'on_mouse_press':
            _user32.SetCapture(self._view_hwnd)
        else:
            _user32.ReleaseCapture()
        x, y = self._get_location(lParam)
        y = self._height - y
        self.dispatch_event(ev, x / self._mouse_scale, y / self._mouse_scale, button, self._get_modifiers())
        return 0

    @ViewEventHandler
    @Win32EventHandler(constants.WM_LBUTTONDOWN)
    def _event_lbuttondown(self, msg: int, wParam: int, lParam: int) -> int:
        return self._event_mousebutton(
            'on_mouse_press', mouse.LEFT, lParam)

    @ViewEventHandler
    @Win32EventHandler(constants.WM_LBUTTONUP)
    def _event_lbuttonup(self, msg: int, wParam: int, lParam: int) -> int:
        return self._event_mousebutton(
            'on_mouse_release', mouse.LEFT, lParam)

    @ViewEventHandler
    @Win32EventHandler(constants.WM_MBUTTONDOWN)
    def _event_mbuttondown(self, msg: int, wParam: int, lParam: int) -> int:
        return self._event_mousebutton(
            'on_mouse_press', mouse.MIDDLE, lParam)

    @ViewEventHandler
    @Win32EventHandler(constants.WM_MBUTTONUP)
    def _event_mbuttonup(self, msg: int, wParam: int, lParam: int) -> int:
        return self._event_mousebutton(
            'on_mouse_release', mouse.MIDDLE, lParam)

    @ViewEventHandler
    @Win32EventHandler(constants.WM_RBUTTONDOWN)
    def _event_rbuttondown(self, msg: int, wParam: int, lParam: int) -> int:
        return self._event_mousebutton(
            'on_mouse_press', mouse.RIGHT, lParam)

    @ViewEventHandler
    @Win32EventHandler(constants.WM_RBUTTONUP)
    def _event_rbuttonup(self, msg: int, wParam: int, lParam: int) -> int:
        return self._event_mousebutton(
            'on_mouse_release', mouse.RIGHT, lParam)

    @ViewEventHandler
    @Win32EventHandler(constants.WM_XBUTTONDOWN)
    def _event_xbuttondown(self, msg: int, wParam: int, lParam: int) -> int:
        if c_short(wParam >> 16).value == 1:
            button = mouse.MOUSE4
        if c_short(wParam >> 16).value == 2:
            button = mouse.MOUSE5
        return self._event_mousebutton(
            'on_mouse_press', button, lParam)

    @ViewEventHandler
    @Win32EventHandler(constants.WM_XBUTTONUP)
    def _event_xbuttonup(self, msg: int, wParam: int, lParam: int) -> int:
        if c_short(wParam >> 16).value == 1:
            button = mouse.MOUSE4
        if c_short(wParam >> 16).value == 2:
            button = mouse.MOUSE5
        return self._event_mousebutton(
            'on_mouse_release', button, lParam)

    @Win32EventHandler(constants.WM_MOUSEWHEEL)
    def _event_mousewheel(self, msg: int, wParam: int, lParam: int) -> int:
        delta = c_short(wParam >> 16).value
        self.dispatch_event('on_mouse_scroll',
                            self._mouse_x, self._mouse_y, 0, delta / float(constants.WHEEL_DELTA))
        return 0

    @Win32EventHandler(constants.WM_CLOSE)
    def _event_close(self, msg: int, wParam: int, lParam: int) -> int:
        self.dispatch_event('on_close')
        return 0

    @ViewEventHandler
    @Win32EventHandler(constants.WM_PAINT)
    def _event_paint(self, msg: int, wParam: int, lParam: int) -> None:
        self.dispatch_event('on_expose')

        # Validating the window using ValidateRect or ValidateRgn
        # doesn't clear the paint message when more than one window
        # is open [why?]; defer to DefWindowProc instead.
        return

    @Win32EventHandler(constants.WM_SIZING)
    def _event_sizing(self, msg: int, wParam: int, lParam: int) -> int:
        from pyglet import app
        if app.event_loop is not None:
            app.event_loop.enter_blocking()
        return 1

    @Win32EventHandler(constants.WM_SIZE)
    def _event_size(self, msg: int, wParam: int, lParam: int) -> int | None:
        if not self._dc:
            # Ignore window creation size event (appears for fullscreen
            # only) -- we haven't got DC or HWND yet.
            return None

        if wParam == constants.SIZE_MINIMIZED:
            # Minimized, not resized.
            self._hidden = True
            self.dispatch_event('on_hide')
            return 0
        if self._hidden:
            # Restored
            self._hidden = False
            self.dispatch_event('on_show')
        w, h = self._get_location(lParam)
        if not self._fullscreen:
            self._width, self._height = w, h
        self._update_view_location(self._width, self._height)

        if self._exclusive_mouse:
            self._update_clipped_cursor()

        self.switch_to()
        self.dispatch_event('_on_internal_resize', self._width, self._height)
        return 0

    @Win32EventHandler(constants.WM_SYSCOMMAND)
    def _event_syscommand(self, msg: int, wParam: int, lParam: int) -> int | None:
        # check for ALT key to prevent app from hanging because there is
        # no windows menu bar
        if wParam == constants.SC_KEYMENU and lParam & (1 >> 16) <= 0:
            return 0

        return None

    @Win32EventHandler(constants.WM_MOVE)
    def _event_move(self, msg: int, wParam: int, lParam: int) -> int:
        x, y = self._get_location(lParam)
        self.dispatch_event('on_move', x / self._mouse_scale, y / self._mouse_scale)
        return 0

    @Win32EventHandler(constants.WM_SETCURSOR)
    def _event_setcursor(self, msg: int, wParam: int, lParam: int) -> int | None:
        if self._exclusive_mouse and not self._mouse_platform_visible:
            lo, hi = self._get_location(lParam)
            if lo == constants.HTCLIENT:  # In frame
                self._set_cursor_visibility(False)
                return 1
            elif lo in (constants.HTCAPTION, constants.HTCLOSE, constants.HTMAXBUTTON,  # noqa: RET505
                        constants.HTMINBUTTON):  # Allow in
                self._set_cursor_visibility(True)
                return 1
        return None

    @Win32EventHandler(constants.WM_ENTERSIZEMOVE)
    def _event_entersizemove(self, msg: int, wParam: int, lParam: int) -> None:
        self._moving = True
        from pyglet import app
        if app.event_loop is not None:
            app.event_loop.enter_blocking()

    @Win32EventHandler(constants.WM_EXITSIZEMOVE)
    def _event_exitsizemove(self, msg: int, wParam: int, lParam: int) -> None:
        self._moving = False
        from pyglet import app
        if app.event_loop is not None:
            app.event_loop.exit_blocking()

        if self._exclusive_mouse:
            self._update_clipped_cursor()

    @Win32EventHandler(constants.WM_SETFOCUS)
    def _event_setfocus(self, msg: int, wParam: int, lParam: int) -> int:
        self.dispatch_event('on_activate')
        self._has_focus = True

        if self._exclusive_mouse and _user32.GetAsyncKeyState(constants.VK_LBUTTON):
            self._pending_click = True

        self.set_exclusive_keyboard(self._exclusive_keyboard)
        self.set_exclusive_mouse(self._exclusive_mouse)

        return 0

    @Win32EventHandler(constants.WM_KILLFOCUS)
    def _event_killfocus(self, msg: int, wParam: int, lParam: int) -> int:
        self.dispatch_event('on_deactivate')
        self._has_focus = False

        exclusive_keyboard = self._exclusive_keyboard
        exclusive_mouse = self._exclusive_mouse
        # Disable both exclusive keyboard and mouse
        self.set_exclusive_keyboard(False)
        self.set_exclusive_mouse(False)

        # Reset shift state on Window focus loss.
        for symbol in self._keyboard_state:
            self._keyboard_state[symbol] = False

        # But save desired state and note that we lost focus
        # This will allow to reset the correct mode once we regain focus
        self._exclusive_keyboard = exclusive_keyboard
        self._exclusive_keyboard_focus = False
        self._exclusive_mouse = exclusive_mouse
        self._exclusive_mouse_focus = False
        return 0

    @Win32EventHandler(constants.WM_GETMINMAXINFO)
    def _event_getminmaxinfo(self, msg: int, wParam: int, lParam: int) -> int:
        info = MINMAXINFO.from_address(lParam)

        if self._minimum_size:
            info.ptMinTrackSize.x, info.ptMinTrackSize.y = \
                self._client_to_window_size_dpi(*self._minimum_size)
        if self._maximum_size:
            info.ptMaxTrackSize.x, info.ptMaxTrackSize.y = \
                self._client_to_window_size_dpi(*self._maximum_size)
        return 0

    @Win32EventHandler(constants.WM_ERASEBKGND)
    def _event_erasebkgnd(self, msg: int, wParam: int, lParam: int) -> int:
        # Prevent flicker during resize; but erase bkgnd if we're fullscreen.
        if self._fullscreen:
            return 0

        return 1

    @ViewEventHandler
    @Win32EventHandler(constants.WM_ERASEBKGND)
    def _event_erasebkgnd_view(self, msg: int, wParam: int, lParam: int) -> int:
        # Prevent flicker during resize.
        return 1

    @Win32EventHandler(constants.WM_DROPFILES)
    def _event_drop_files(self, msg: int, wParam: int, lParam: int) -> int:
        drop = wParam

        # Get the count so we can handle multiple files.
        file_count = _shell32.DragQueryFileW(drop, 0xFFFFFFFF, None, 0)

        # Get where drop point was.
        point = POINT()
        _shell32.DragQueryPoint(drop, byref(point))

        paths = []
        for i in range(file_count):
            length = _shell32.DragQueryFileW(drop, i, None, 0)  # Length of string.

            buffer = create_unicode_buffer(length + 1)

            _shell32.DragQueryFileW(drop, i, buffer, length + 1)

            paths.append(buffer.value)

        _shell32.DragFinish(drop)

        # Reverse Y and call event.
        self.dispatch_event('on_file_drop', point.x, self._height - point.y, paths)
        return 0

    @Win32EventHandler(constants.WM_GETDPISCALEDSIZE)
    def _event_dpi_scaled_size(self, msg: int, wParam: int, lParam: int) -> int | None:
        if pyglet.options.dpi_scaling in ("scaled", "stretch"):
            return None

        size = cast(lParam, POINTER(SIZE)).contents

        dpi = wParam

        if constants.WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
            current = RECT()
            result = RECT()

            # Size between current size and future.
            _user32.AdjustWindowRectExForDpi(byref(current),
                                             self._ws_style, False, self._ex_ws_style,
                                             _user32.GetDpiForWindow(self._hwnd))

            _user32.AdjustWindowRectExForDpi(byref(result),
                                             self._ws_style, False, self._ex_ws_style, dpi)

            size.cx += (result.right - result.left) - (current.right - current.left)
            size.cy += (result.bottom - result.top) - (current.bottom - current.top)
            return 1

        return None

    @Win32EventHandler(constants.WM_DPICHANGED)
    def _event_dpi_change(self, msg: int, wParam: int, lParam: int) -> int:
        y_dpi, x_dpi = self._get_location(wParam)

        scale = x_dpi / constants.USER_DEFAULT_SCREEN_DPI

        self._dpi = x_dpi

        if not self._fullscreen and \
                (pyglet.options.dpi_scaling != "real" or constants.WINDOWS_10_CREATORS_UPDATE_OR_GREATER):
            suggested_rect = cast(lParam, POINTER(RECT)).contents

            x = suggested_rect.left
            y = suggested_rect.top
            width = suggested_rect.right - suggested_rect.left
            height = suggested_rect.bottom - suggested_rect.top

            _user32.SetWindowPos(self._hwnd, 0, x, y, width, height,
                                 constants.SWP_NOZORDER | constants.SWP_NOOWNERZORDER | constants.SWP_NOACTIVATE)

        if pyglet.options.dpi_scaling == "stretch":
            self._mouse_scale = scale

        self.switch_to()
        self.dispatch_event('_on_internal_scale', scale, x_dpi)
        return 1



__all__ = ['Win32EventHandler', 'Win32Window']
