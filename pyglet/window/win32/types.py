#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *

BOOL = c_int
DWORD = c_uint32

HANDLE = c_void_p
HWND = HANDLE
HMONITOR = HANDLE
HGLOBAL = HANDLE
HDC = HANDLE
LPARAM = c_long

WNDPROC = WINFUNCTYPE(c_long, c_int, c_uint, c_int, c_int)

class RECT(Structure):
    _fields_ = [
        ('left', c_long),
        ('top', c_long),
        ('right', c_long),
        ('bottom', c_long)
    ]

class WNDCLASS(Structure):
    _fields_ = [
        ('style', c_uint),
        ('lpfnWndProc', WNDPROC),
        ('cbClsExtra', c_int),
        ('cbWndExtra', c_int),
        ('hInstance', c_int),
        ('hIcon', c_int),
        ('hCursor', c_int),
        ('hbrBackground', c_int),
        ('lpszMenuName', c_char_p),
        ('lpszClassName', c_char_p)
    ]

class POINT(Structure):
    _fields_ = [
        ('x', c_long),
        ('y', c_long)
    ]

class MSG(Structure):
    _fields_ = [
        ('hwnd', c_int),
        ('message', c_uint),
        ('wParam', c_int),
        ('lParam', c_int),
        ('time', c_int),
        ('pt', POINT)
    ]

class PIXELFORMATDESCRIPTOR(Structure):
    _fields_ = [
        ('nSize', c_ushort),
        ('nVersion', c_ushort),
        ('dwFlags', c_ulong),
        ('iPixelType', c_ubyte),
        ('cColorBits', c_ubyte),
        ('cRedBits', c_ubyte),
        ('cRedShift', c_ubyte),
        ('cGreenBits', c_ubyte),
        ('cGreenShift', c_ubyte),
        ('cBlueBits', c_ubyte),
        ('cBlueShift', c_ubyte),
        ('cAlphaBits', c_ubyte),
        ('cAlphaShift', c_ubyte),
        ('cAccumBits', c_ubyte),
        ('cAccumRedBits', c_ubyte),
        ('cAccumRedShift', c_ubyte),
        ('cAccumGreenBits', c_ubyte),
        ('cAccumGreenShift', c_ubyte),
        ('cAccumBlueBits', c_ubyte),
        ('cAccumBlueShift', c_ubyte),
        ('cAccumAlphaBits', c_ubyte),
        ('cAccumAlphaShift', c_ubyte),
        ('cDepthBits', c_ubyte),
        ('cStencilBits', c_ubyte),
        ('cAuxBuffers', c_ubyte),
        ('iLayerType', c_ubyte),
        ('bReserved', c_ubyte),
        ('dwLayerMask', c_ulong),
        ('dwVisibleMask', c_ulong),
        ('dwDamageMask', c_ulong)
    ]

class TRACKMOUSEEVENT(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('dwFlags', DWORD),
        ('hwndTrack', HWND),
        ('dwHoverTime', DWORD)
    ]

class MINMAXINFO(Structure):
    _fields_ = [
        ('ptReserved', POINT),
        ('ptMaxSize', POINT),
        ('ptMaxPosition', POINT),
        ('ptMinTrackSize', POINT),
        ('ptMaxTrackSize', POINT)
    ]
