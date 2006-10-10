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

class Win32WindowFactory(BaseWindowFactory):
    def create_config_prototype(self):
        return Win32GLConfig()

    def create_window(self, width, height):
        return Win32Window(width, height)

    def get_config_matches(self, window):
        return self.config.get_matches(window._dc)

    def create_context(self, window, config, share_context=None):
        _gdi32.SetPixelFormat(window._dc, config._pf, byref(config._pfd))
        context = wglCreateContext(window._dc)
        return context

class Win32Window(BaseWindow):
    def __init__(self, width, height):
        super(Win32Window, self).__init__(width, height)
        handle = _kernel32.GetModuleHandleA(c_int(0))
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
        wglMakeCurrent(self._dc, self.context)

    def flip(self):
        wglSwapLayerBuffers(self._dc, WGL_SWAP_MAIN_PLANE)

    def dispatch_events(self):
        msg = MSG()
        while _user32.PeekMessageA(byref(msg), 0, 0, 0, PM_REMOVE):
            _user32.TranslateMessage(byref(msg))
            _user32.DispatchMessageA(byref(msg))

    def set_title(self, title):
        self._title = title

    def get_title(self):
        return self._title

class Win32GLConfig(BaseGLConfig):
    def __init__(self, _hdc=0, _pf=0):
        super(Win32GLConfig, self).__init__()
        self._hdc = _hdc
        self._pf = _pf
        if self._hdc and self._pf:
            self._pfd = PIXELFORMATDESCRIPTOR()
            _gdi32.DescribePixelFormat(self._hdc, 
                self._pf, sizeof(PIXELFORMATDESCRIPTOR), byref(self._pfd))
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

    def get_matches(self, hdc):
        pfd = PIXELFORMATDESCRIPTOR()
        pfd.nSize = sizeof(PIXELFORMATDESCRIPTOR)
        pfd.nVersion = 1
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL

        if self._attributes.get('doublebuffer', False):
            pfd.dwFlags |= PFD_DOUBLEBUFFER
        else:
            pfd.dwFlags |= PFD_DOUBLEBUFFER_DONTCARE

        if self._attributes.get('stereo', False):
            pfd.dwFlags |= PFD_STEREO
        else:
            pfd.dwFlags |= PFD_STEREO_DONTCARE

        if self._attributes.get('swap_copy', False):
            pfd.dwFlags |= PFD_SWAP_COPY
        if self._attributes.get('swap_exchange', False):
            pfd.dwFlags |= PFD_SWAP_EXCHANGE

        if not self._attributes.get('depth_size', 0):
            pfd.dwFlags |= PFD_DEPTH_DONTCARE

        pfd.iPixelType = PFD_TYPE_RGBA
        pfd.cColorBits = self._attributes.get('buffer_size', 0)
        pfd.cRedBits = self._attributes.get('red_size', 0)
        pfd.cGreenBits = self._attributes.get('green_size', 0)
        pfd.cBlueBits = self._attributes.get('blue_size', 0)
        pfd.cAlphaBits = self._attributes.get('alpha_size', 0)
        pfd.cAccumRedBits = self._attributes.get('accum_red_size', 0)
        pfd.cAccumGreenBits = self._attributes.get('accum_green_size', 0)
        pfd.cAccumBlueBits = self._attributes.get('accum_blue_size', 0)
        pfd.cAccumAlphaBits = self._attributes.get('accum_alpha_size', 0)
        pfd.cDepthBits = self._attributes.get('depth_size', 0)
        pfd.cStencilBits = self._attributes.get('stencil_size', 0)
        pfd.cAuxBuffers = self._attributes.get('aux_buffers', 0)

        pf = _gdi32.ChoosePixelFormat(hdc, byref(pfd))
        if pf:
            return [Win32GLConfig(hdc, pf)]
        else:
            return []

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
        event = EVENT_KEYRELEASE
    else:
        event = EVENT_KEYPRESS

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
