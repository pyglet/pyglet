#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
import unicodedata

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.window.win32.constants import *
from pyglet.window.win32.key import *
from pyglet.window.win32.types import *
from pyglet.window.win32.WGL import *

_gdi32 = windll.gdi32
_kernel32 = windll.kernel32
_user32 = windll.user32

_user32.GetKeyState.restype = c_short

class Win32Exception(WindowException):
    pass

class Win32Platform(BasePlatform):
    def get_screens(self, factory):
        screens = []
        def enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            r = lprcMonitor.contents
            width = r.right - r.left
            height = r.bottom - r.top
            screens.append(
                Win32Screen(hMonitor, r.left, r.top, width, height))
            return True
        enum_proc_type = CFUNCTYPE(BOOL, HMONITOR, HDC, POINTER(RECT), LPARAM)
        enum_proc_ptr = enum_proc_type(enum_proc)
        _user32.EnumDisplayMonitors(NULL, NULL, enum_proc_ptr, 0)
        return screens

    def create_configs(self, factory):
        attributes = factory.get_gl_attributes()

        pfd = PIXELFORMATDESCRIPTOR()
        pfd.nSize = sizeof(PIXELFORMATDESCRIPTOR)
        pfd.nVersion = 1
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL

        if attributes.get('doublebuffer', False):
            pfd.dwFlags |= PFD_DOUBLEBUFFER
        else:
            pfd.dwFlags |= PFD_DOUBLEBUFFER_DONTCARE

        if attributes.get('stereo', False):
            pfd.dwFlags |= PFD_STEREO
        else:
            pfd.dwFlags |= PFD_STEREO_DONTCARE

        if attributes.get('swap_copy', False):
            pfd.dwFlags |= PFD_SWAP_COPY
        if attributes.get('swap_exchange', False):
            pfd.dwFlags |= PFD_SWAP_EXCHANGE

        if not attributes.get('depth_size', 0):
            pfd.dwFlags |= PFD_DEPTH_DONTCARE

        pfd.iPixelType = PFD_TYPE_RGBA
        pfd.cColorBits = attributes.get('buffer_size', 0)
        pfd.cRedBits = attributes.get('red_size', 0)
        pfd.cGreenBits = attributes.get('green_size', 0)
        pfd.cBlueBits = attributes.get('blue_size', 0)
        pfd.cAlphaBits = attributes.get('alpha_size', 0)
        pfd.cAccumRedBits = attributes.get('accum_red_size', 0)
        pfd.cAccumGreenBits = attributes.get('accum_green_size', 0)
        pfd.cAccumBlueBits = attributes.get('accum_blue_size', 0)
        pfd.cAccumAlphaBits = attributes.get('accum_alpha_size', 0)
        pfd.cDepthBits = attributes.get('depth_size', 0)
        pfd.cStencilBits = attributes.get('stencil_size', 0)
        pfd.cAuxBuffers = attributes.get('aux_buffers', 0)

        # No window created yet, so lets create a config based on
        # the DC of the entire screen.
        hdc = _user32.GetDC(0)

        pf = _gdi32.ChoosePixelFormat(hdc, byref(pfd))
        if pf:
            return [Win32Config(hdc, pf)]
        else:
            return []

    def create_context(self, factory):
        # The context can't be created until we have the DC of the
        # window.  It's _possible_ that this could screw things up
        # (for example, destroying the share context before the new
        # window is created), but these are unlikely and not in the
        # ordinary workflow.
        config = factory.get_config()
        share = factory.get_context_share()
        return Win32Context(config, share)

    def create_window(self):
        return Win32Window()

class Win32Screen(BaseScreen):
    def __init__(self, handle, x, y, width, height):
        super(Win32Screen, self).__init__(x, y, width, height)
        self._handle = handle

class Win32Config(BaseGLConfig):
    def __init__(self, hdc, pf):
        self._hdc = hdc
        self._pf = pf
        self._pfd = PIXELFORMATDESCRIPTOR()
        _gdi32.DescribePixelFormat(self._hdc, 
            self._pf, sizeof(PIXELFORMATDESCRIPTOR), byref(self._pfd))

        self._attributes = {}
        self._attributes['doublebuffer'] = \
            bool(self._pfd.dwFlags & PFD_DOUBLEBUFFER)
        self._attributes['stereo'] = bool(self._pfd.dwFlags & PFD_STEREO)
        self._attributes['buffer_size'] = self._pfd.cColorBits
        self._attributes['red_size'] = self._pfd.cRedBits
        self._attributes['green_size'] = self._pfd.cGreenBits
        self._attributes['blue_size'] = self._pfd.cBlueBits
        self._attributes['alpha_size'] = self._pfd.cAlphaBits
        self._attributes['accum_red_size'] = self._pfd.cAccumRedBits
        self._attributes['accum_green_size'] = self._pfd.cAccumGreenBits
        self._attributes['accum_blue_size'] = self._pfd.cAccumBlueBits
        self._attributes['accum_alpha_size'] = self._pfd.cAccumAlphaBits
        self._attributes['depth_size'] = self._pfd.cDepthBits
        self._attributes['stencil_size'] = self._pfd.cStencilBits
        self._attributes['aux_buffers'] = self._pfd.cAuxBuffers

    def get_gl_attributes(self):
        return self._attributes

class Win32Context(BaseGLContext):
    _context = None
    def __init__(self, config, share):
        super(Win32Context, self).__init__()
        self._config = config
        self._share = share

    def _set_window(self, window):
        assert self._context is None
        _gdi32.SetPixelFormat(
            window._dc, self._config._pf, byref(self._config._pfd))
        self._context = wglCreateContext(window._dc)
        if self._share:
            assert self._share._context is not None
            wglShareLists(self._share._context, self._context)

    def destroy(self):
        wglDeleteContext(self._context)

_win32_event_handler_types = []

def Win32EventHandler(message):
    def handler_wrapper(f):
        handler = (message, f.__name__)
        _win32_event_handler_types.append(handler)
        return f
    return handler_wrapper

class Win32Mouse(object):
    x = 0
    y = 0

class Win32Window(BaseWindow):
    _window_class = None
    _hwnd = None
    _dc = None
    _wgl_context = None
    _tracking = False
    _hidden = False

    _exclusive_keyboard = False
    _exclusive_mouse = False
    _exclusive_mouse_screen = None
    _ignore_mousemove = False

    _style = 0
    _ex_style = 0
    _minimum_size = None
    _maximum_size = None

    def __init__(self):
        super(Win32Window, self).__init__()

        # Bind event handlers
        self._event_handlers = {}
        for message, func_name in _win32_event_handler_types:
            func = getattr(self, func_name)
            self._event_handlers[message] = func

        self._mouse = Win32Mouse()

    def _context_compatible(self, factory):
        # XXX TODO determine if context config is the same.
        return True

    def create(self, factory):
        # Retain old context if possible
        old_context = None
        if self._context_compatible(factory):
            factory.set_context(self.get_context())
        else:
            old_context = self.get_context()
            factory.set_context_share(old_context)

        super(Win32Window, self).create(factory)
        fullscreen = factory.get_fullscreen()

        # Ensure style is set before determining width/height.
        if fullscreen:
            self._style = WS_POPUP
            self._ex_style = WS_EX_TOPMOST
        else:
            self._style = WS_OVERLAPPEDWINDOW
            self._ex_style = 0

        width, height = self._client_to_window_size(*factory.get_size())
        context = factory.get_context()

        if old_context:
            old_context.destroy()
            self._wgl_context = None

        if not self._window_class:
            white = _gdi32.GetStockObject(WHITE_BRUSH)
            self._window_class = WNDCLASS()
            self._window_class.lpszClassName = 'GenericAppClass'
            self._window_class.lpfnWndProc = WNDPROC(self._wnd_proc)
            self._window_class.style = CS_VREDRAW | CS_HREDRAW
            self._window_class.hInstance = 0
            self._window_class.hIcon = _user32.LoadIconA(0, IDI_APPLICATION)
            self._window_class.hCursor = _user32.LoadCursorA(0, IDC_ARROW)
            self._window_class.hbrBackground = white
            self._window_class.lpszMenuName = None
            self._window_class.cbClsExtra = 0
            self._window_class.cbWndExtra = 0
            if not _user32.RegisterClassA(byref(self._window_class)):
                _check()
        
        if not self._hwnd:
            self._hwnd = _user32.CreateWindowExA(
                self._ex_style,
                self._window_class.lpszClassName,
                '',
                self._style,
                CW_USEDEFAULT,
                CW_USEDEFAULT,
                width,
                height,
                0,
                0,
                self._window_class.hInstance,
                0)

            self._dc = _user32.GetDC(self._hwnd)
        else:
            # Window already exists, update it with new style

            # We need to hide window here, otherwise Windows forgets
            # to redraw the whole screen after leaving fullscreen.
            _user32.ShowWindow(self._hwnd, SW_HIDE)

            _user32.SetWindowLongA(self._hwnd,
                GWL_STYLE,
                self._style)
            _user32.SetWindowLongA(self._hwnd,
                GWL_EXSTYLE,
                self._ex_style)

        if fullscreen:
            hwnd_after = HWND_TOPMOST
        else:
            hwnd_after = HWND_NOTOPMOST

        # Position and size window
        if factory.get_location() != LOCATION_DEFAULT:
            x, y = self._client_to_window_pos(*factory.get_location())
            _user32.SetWindowPos(self._hwnd, hwnd_after,
                x, y, width, height, SWP_FRAMECHANGED)
        else:
            _user32.SetWindowPos(self._hwnd, hwnd_after,
                0, 0, width, height, SWP_NOMOVE | SWP_FRAMECHANGED)

        # Context must be created after window is created.
        if not self._wgl_context:
            context._set_window(self)
            self._wgl_context = context._context


    def close(self):
        super(Win32Window, self).close()
        _user32.DestroyWindow(self._hwnd)
        self._hwnd = None
        self._dc = None
        self._wgl_context = None

    def switch_to(self):
        wglMakeCurrent(self._dc, self._wgl_context)

    def flip(self):
        wglSwapLayerBuffers(self._dc, WGL_SWAP_MAIN_PLANE)

    def set_location(self, x, y):
        x, y = self._client_to_window_pos(x, y)
        _user32.SetWindowPos(self._hwnd, 0, rect.left, rect.top, 0, 0, 
            (SWP_NOZORDER |
             SWP_NOSIZE |
             SWP_NOOWNERZORDER))

    def get_location(self):
        rect = RECT()
        _user32.GetClientRect(self._hwnd, byref(rect))
        _user32.ClientToScreen(self._hwnd, byref(rect))
        return rect.left, rect.top

    def set_size(self, width, height):
        width, height = self._client_to_window_size(width, height)
        _user32.SetWindowPos(self._hwnd, 0, 0, 0, width, height,
            (SWP_NOZORDER |
             SWP_NOMOVE |
             SWP_NOOWNERZORDER))

    def get_size(self):
        rect = RECT()
        _user32.GetClientRect(self._hwnd, byref(rect))
        return rect.right - rect.left, rect.bottom - rect.top

    def set_minimum_size(self, width, height):
        self._minimum_size = width, height

    def set_maximum_size(self, width, height):
        self._maximum_size = width, height

    def activate(self):
        _user32.SetForegroundWindow(self._hwnd)

    def set_visible(self, visible=True):
        if visible:
            _user32.ShowWindow(self._hwnd, SW_SHOW)
            if self._fullscreen:
                self.activate()
        else:
            _user32.ShowWindow(self._hwnd, SW_HIDE)

    def minimize(self):
        _user32.ShowWindow(self._hwnd, SW_MINIMIZE)

    def maximize(self):
        _user32.ShowWindow(self._hwnd, SW_MAXIMIZE)

    def set_caption(self, caption):
        super(Win32Window, self).set_caption(caption)
        _user32.SetWindowTextW(self._hwnd, c_wchar_p(caption))

    def set_exclusive_mouse(self, exclusive=True):
        if self._exclusive_mouse == exclusive:
            return
    
        if exclusive:
            # Move mouse to the center of the window.
            p = POINT()
            rect = RECT()
            _user32.GetClientRect(self._hwnd, byref(rect))
            _user32.MapWindowPoints(self._hwnd, HWND_DESKTOP, byref(rect), 2)
            p.x = (rect.left + rect.right) / 2
            p.y = (rect.top + rect.bottom) / 2

            # This is the point the mouse will be kept at while in exclusive
            # mode.
            self._exclusive_mouse_screen = p.x, p.y
            self._ignore_mousemove = True
            _user32.SetCursorPos(p.x, p.y)

            # Clip to client area, to prevent large mouse movements taking
            # it outside the client area.
            _user32.ClipCursor(byref(rect))
        else:
            # Release clip
            _user32.ClipCursor(c_void_p())

        _user32.ShowCursor(not exclusive)
        self._exclusive_mouse = exclusive

    def set_exclusive_keyboard(self, exclusive=True):
        if self._exclusive_keyboard == exclusive:
            return

        if exclusive:
            _user32.RegisterHotKey(self._hwnd, 0, WIN32_MOD_ALT, VK_TAB)
        else:
            for i in range(3):
                _user32.UnregisterHotKey(self._hwnd, i)

        self._exclusive_keyboard = exclusive

    # Private util

    def _client_to_window_size(self, width, height):
        rect = RECT()
        rect.left = 0
        rect.top = 0
        rect.right = width
        rect.bottom = height
        _user32.AdjustWindowRectEx(byref(rect),
            self._style, False, self._ex_style)
        return rect.right - rect.left, rect.bottom - rect.top

    def _client_to_window_pos(self, x, y):
        rect = RECT()
        rect.left = x
        rect.top = y
        _user32.AdjustWindowRectEx(byref(rect),
            self._style, False, self._ex_style)
        return rect.left, rect.top

    # Event dispatching

    def dispatch_events(self):
        msg = MSG()
        while _user32.PeekMessageA(byref(msg), self._hwnd, 0, 0, PM_REMOVE):
            _user32.TranslateMessage(byref(msg))
            _user32.DispatchMessageA(byref(msg))

    def _wnd_proc(self, hwnd, msg, wParam, lParam):
        event_handler = self._event_handlers.get(msg, None)
        result = None
        if event_handler:
            result = event_handler(msg, wParam, lParam)
        if result is None:
            result = _user32.DefWindowProcA(c_int(hwnd), c_int(msg),
                c_int(wParam), c_int(lParam)) 
        return result

    # Event handlers

    def _get_modifiers(self, key_lParam=0):
        modifiers = 0
        if _user32.GetKeyState(VK_SHIFT) & 0xff00:
            modifiers |= MOD_SHIFT
        if _user32.GetKeyState(VK_CONTROL) & 0xff00:
            modifiers |= MOD_CTRL
        if _user32.GetKeyState(VK_LWIN) & 0xff00:
            modifiers |= MOD_WINDOWS
        if _user32.GetKeyState(VK_CAPITAL) & 0x00ff:    # toggle
            modifiers |= MOD_CAPSLOCK
        if _user32.GetKeyState(VK_NUMLOCK) & 0x00ff:    # toggle
            modifiers |= MOD_NUMLOCK
        if key_lParam & (1 << 29):
            modifiers |= MOD_ALT
        return modifiers

    @staticmethod
    def _get_location(lParam):
        x = c_int16(lParam & 0xffff).value
        y = c_int16(lParam >> 16).value
        return x, y

    @Win32EventHandler(WM_KEYDOWN)
    @Win32EventHandler(WM_KEYUP)
    @Win32EventHandler(WM_SYSKEYDOWN)
    @Win32EventHandler(WM_SYSKEYUP)
    def _event_key(self, msg, wParam, lParam):
        if lParam & (1 << 30):
            if msg not in (WM_KEYUP, WM_SYSKEYUP):
                return 0    # key repeat
            event = EVENT_KEY_RELEASE
        else:
            event = EVENT_KEY_PRESS

        symbol = keymap.get(wParam, None)
        if symbol:
            if symbol == K_LCTRL and lParam & (1 << 24):
                symbol = K_RCTRL
            if symbol == K_LALT and lParam & (1 << 24):
                symbol = K_RALT
            elif symbol == K_LSHIFT:
                pass # TODO: some magic with getstate to find out if it's the
                     # right or left shift key. 
            
            self.dispatch_event(event, symbol, self._get_modifiers(lParam))

        # Send on to DefWindowProc if not exclusive.
        if self._exclusive_keyboard:
            return 0
        else:
            return None

    @Win32EventHandler(WM_CHAR)
    def _event_char(self, msg, wParam, lParam):
        text = unichr(wParam)
        if unicodedata.category(text) != 'Cc' or text == '\r':
            self.dispatch_event(EVENT_TEXT, text)
        return 0

    @Win32EventHandler(WM_MOUSEMOVE)
    def _event_mousemove(self, msg, wParam, lParam):
        x, y = self._get_location(lParam)
        if self._ignore_mousemove:
            # Ignore the event caused by SetCursorPos
            self._ignore_mousemove = False
            return 0

        if self._exclusive_mouse:
            # Reset mouse position (so we don't hit the edge of the screen).
            self._ignore_mousemove = True
            _user32.SetCursorPos(*self._exclusive_mouse_screen)
            
        dx = x - self._mouse.x
        dy = y - self._mouse.y

        if not self._tracking:
            # There is no WM_MOUSEENTER message (!), so fake it from the
            # first WM_MOUSEMOVE event after leaving.  Use self._tracking
            # to determine when to recreate the tracking structure after
            # re-entering (to track the next WM_MOUSELEAVE).
            self.dispatch_event(EVENT_MOUSE_ENTER, x, y)
            self._tracking = True
            track = TRACKMOUSEEVENT()
            track.cbSize = sizeof(track)
            track.dwFlags = TME_LEAVE
            track.hwndTrack = self._hwnd
            _user32.TrackMouseEvent(byref(track))

        self._mouse.x = x
        self._mouse.y = y
        
        buttons = 0
        if wParam & MK_LBUTTON:
            buttons |= MOUSE_LEFT_BUTTON
        if wParam & MK_MBUTTON:
            buttons |= MOUSE_MIDDLE_BUTTON
        if wParam & MK_RBUTTON:
            buttons |= MOUSE_RIGHT_BUTTON

        if buttons:
            # Drag event
            modifiers = self._get_modifiers()
            self.dispatch_event(EVENT_MOUSE_DRAG, 
                x, y, dx, dy, buttons, modifiers)
        else:
            # Motion event
            self.dispatch_event(EVENT_MOUSE_MOTION, x, y, dx, dy)
        return 0

    @Win32EventHandler(WM_MOUSELEAVE)
    def _event_mouseleave(self, msg, wParam, lParam):
        point = POINT()
        _user32.GetCursorPos(byref(point))
        _user32.ScreenToClient(self._hwnd, byref(point))
        self._tracking = False
        self.dispatch_event(EVENT_MOUSE_LEAVE, point.x, point.y)
        return 0

    def _event_mousebutton(self, event, button, lParam):
        if event == EVENT_MOUSE_PRESS:
            _user32.SetCapture(self._hwnd)
        else:
            #_user32.ReleaseCapture()
            pass
        x, y = self._get_location(lParam)
        self.dispatch_event(event, button, x, y, self._get_modifiers())
        return 0

    @Win32EventHandler(WM_LBUTTONDOWN)
    def _event_lbuttondown(self, msg, wParam, lParam):
        return self._event_mousebutton(
            EVENT_MOUSE_PRESS, MOUSE_LEFT_BUTTON, lParam)

    @Win32EventHandler(WM_LBUTTONUP)
    def _event_lbuttonup(self, msg, wParam, lParam):
        return self._event_mousebutton(
            EVENT_MOUSE_RELEASE, MOUSE_LEFT_BUTTON, lParam)

    @Win32EventHandler(WM_MBUTTONDOWN)
    def _event_mbuttondown(self, msg, wParam, lParam):
        return self._event_mousebutton(
            EVENT_MOUSE_PRESS, MOUSE_MIDDLE_BUTTON, lParam)

    @Win32EventHandler(WM_MBUTTONUP)
    def _event_mbuttonup(self, msg, wParam, lParam):
        return self._event_mousebutton(
            EVENT_MOUSE_RELEASE, MOUSE_MIDDLE_BUTTON, lParam)

    @Win32EventHandler(WM_RBUTTONDOWN)
    def _event_rbuttondown(self, msg, wParam, lParam):
        return self._event_mousebutton(
            EVENT_MOUSE_PRESS, MOUSE_RIGHT_BUTTON, lParam)

    @Win32EventHandler(WM_RBUTTONUP)
    def _event_rbuttonup(self, msg, wParam, lParam):
        return self._event_mousebutton(
            EVENT_MOUSE_RELEASE, MOUSE_RIGHT_BUTTON, lParam)

    @Win32EventHandler(WM_MOUSEWHEEL)
    def _event_mousewheel(self, msg, wParam, lParam):
        delta = c_short(wParam >> 16).value
        self.dispatch_event(EVENT_MOUSE_SCROLL, 0, float(delta) / WHEEL_DELTA)
        return 0

    @Win32EventHandler(WM_CLOSE)
    def _event_close(self, msg, wParam, lParam):
        self.dispatch_event(EVENT_CLOSE)
        return 0

    @Win32EventHandler(WM_PAINT)
    def _event_paint(self, msg, wParam, lParam):
        self.dispatch_event(EVENT_EXPOSE)
        # Validating the window using ValidateRect or ValidateRgn
        # doesn't clear the paint message when more than one window
        # is open [why?]; defer to DefWindowProc instead.
        return None

    @Win32EventHandler(WM_SIZE)
    def _event_size(self, msg, wParam, lParam):
        if wParam == SIZE_MINIMIZED:
            # Minimized, not resized.
            self._hidden = True
            self.dispatch_event(EVENT_HIDE)
            return 0
        if self._hidden:
            # Restored
            self._hidden = False
            self.dispatch_event(EVENT_SHOW)
        w, h = self._get_location(lParam)
        self.dispatch_event(EVENT_RESIZE, w, h)
        return 0

    @Win32EventHandler(WM_MOVE)
    def _event_move(self, msg, wParam, lParam):
        x, y = self._get_location(lParam)
        self.dispatch_event(EVENT_MOVE, x, y)
        return 0

    '''
    # Alternative to using WM_SETFOCUS and WM_KILLFOCUS.  Which
    # is better?

    @Win32EventHandler(WM_ACTIVATE)
    def _event_activate(self, msg, wParam, lParam):
        if wParam & 0xffff == WA_INACTIVE:
            self.dispatch_event(EVENT_DEACTIVATE)
        else:
            self.dispatch_event(EVENT_ACTIVATE)
            _user32.SetFocus(self._hwnd)
        return 0
    '''

    @Win32EventHandler(WM_SETFOCUS)
    def _event_setfocus(self, msg, wParam, lParam):
        self.dispatch_event(EVENT_ACTIVATE)
        return 0

    @Win32EventHandler(WM_KILLFOCUS)
    def _event_killfocus(self, msg, wParam, lParam):
        self.dispatch_event(EVENT_DEACTIVATE)
        return 0

    @Win32EventHandler(WM_GETMINMAXINFO)
    def _event_getminmaxinfo(self, msg, wParam, lParam):
        info = MINMAXINFO.from_address(lParam)
        if self._minimum_size:
            info.ptMinTrackSize.x, info.ptMinTrackSize.y = \
                self._client_to_window_size(*self._minimum_size)
        if self._maximum_size:
            info.ptMaxTrackSize.x, info.ptMaxTrackSize.y = \
                self._client_to_window_size(*self._maximum_size)
        return 0

    @Win32EventHandler(WM_ERASEBKGND)
    def _event_erasebkgnd(self, msg, wParam, lParam):
        # Prevent flicker during resize.
        return 0

def _check():
    dw = _kernel32.GetLastError()
    if dw != 0:
        msg = create_string_buffer(256)
        _kernel32.FormatMessageA(FORMAT_MESSAGE_FROM_SYSTEM,
                              c_void_p(),
                              dw,
                              0,
                              msg,
                              len(msg),
                              c_void_p())
        raise Win32Exception(msg.value)
