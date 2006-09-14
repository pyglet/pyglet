#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *

from pyglet.window import *
from pyglet.window.win32.constants import *

_user32 = windll.user32
_kernel32 = windll.kernel32

class Win32Exception(WindowException):
    pass

class Win32WindowFactory(BaseWindowFactory):
    def __init__(self):
        pass

    def create_window(self, width=640, height=480):
        window = Win32Window(width, height)
        return window

class Win32Window(BaseWindow):
    def __init__(self, width, height):
        self._handle = _kernel32.GetModuleHandle(c_void_p())
        self._hwnd = _user32.CreateWindowEx(0,
            'MainWClass',
            'Main Window',
            WS_OVERLAPPEDWINDOW,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            width,
            height,
            c_void_p(),
            c_void_p(),
            self._handle,
            c_void_p())

        _user32.ShowWindow(self._hwnd, SW_SHOWDEFAULT)

    def close(self):
        pass

    def switch_to(self):
        pass

    def flip(self):
        pass

    def get_events(self):
        pass

    def set_title(self, title):
        self._title = title

    def get_title(self):
        return self._title

