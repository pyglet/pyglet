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
            screens.append(
                Win32Screen(hMonitor, r.left, r.top, r.width, r.height))
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

class Win32Window(BaseWindow):
    _window_class = None
    _hwnd = None
    _dc = None
    _wgl_context = None

    def __init__(self):
        super(Win32Window, self).__init__()

    def create(self, factory):
        super(Win32Window, self).create(factory)

        width, height = factory.get_size()
        context = factory.get_context()

        #handle = _kernel32.GetModuleHandleA(c_int(0))
        handle = 0
        self._window_class = WNDCLASS()
        self._window_class.lpszClassName = 'GenericAppClass'
        self._window_class.lpfnWndProc = WNDPROC(self._wnd_proc)
        self._window_class.style = CS_VREDRAW | CS_HREDRAW
        self._window_class.hInstance = handle
        self._window_class.hIcon = _user32.LoadIconA(0, IDI_APPLICATION)
        self._window_class.hCursor = _user32.LoadCursorA(0, IDC_ARROW)
        self._window_class.hbrBackground = _gdi32.GetStockObject(WHITE_BRUSH)
        self._window_class.lpszMenuName = None
        self._window_class.cbClsExtra = 0
        self._window_class.cbWndExtra = 0
        if not _user32.RegisterClassA(byref(self._window_class)):
            _check()

        self._hwnd = _user32.CreateWindowExA(0,
            self._window_class.lpszClassName,
            'pyglet window',
            WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_CLIPSIBLINGS,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            width,
            height,
            0,
            0,
            self._window_class.hInstance,
            0)

        self._dc = _user32.GetDC(self._hwnd)

        # Now we have enough to create the context
        context._set_window(self)
        self._wgl_context = context._context

        _user32.ShowWindow(self._hwnd, SW_SHOWDEFAULT)
        _user32.UpdateWindow(self._hwnd)

    def _wnd_proc(self, hwnd, msg, wParam, lParam):
        event_dispatcher = _event_dispatchers.get(msg, None)
        if event_dispatcher:
            result = event_dispatcher(self, msg, wParam, lParam)
        else:
            result = _user32.DefWindowProcA(c_int(hwnd), c_int(msg),
                c_int(wParam), c_int(lParam)) 
        return result

    def close(self):
        pass

    def switch_to(self):
        wglMakeCurrent(self._dc, self._wgl_context)

    def flip(self):
        wglSwapLayerBuffers(self._dc, WGL_SWAP_MAIN_PLANE)

    def dispatch_events(self):
        msg = MSG()
        while _user32.PeekMessageA(byref(msg), 0, 0, 0, PM_REMOVE):
            _user32.TranslateMessage(byref(msg))
            _user32.DispatchMessageA(byref(msg))

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

def _dispatch_key(window, msg, wParam, lParam):
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
        if lParam & (1 << 29):
            modifiers |= MOD_ALT

        window.dispatch_event(event, symbol, modifiers)
    return 0

def _dispatch_char(window, msg, wParam, lParam):
    text = unichr(wParam)
    if unicodedata.category(text) != 'Cc' or text == '\r':
        window.dispatch_event(EVENT_TEXT, text)
    return 0

_event_dispatchers = {
    WM_KEYDOWN: _dispatch_key,
    WM_KEYUP: _dispatch_key,
    WM_SYSKEYDOWN: _dispatch_key,
    WM_SYSKEYUP: _dispatch_key,
    WM_CHAR: _dispatch_char,
}
