#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes as _ctypes

_wgl = _ctypes.windll.opengl32

def _get_function(name, argtypes, rtype):
    try:
        func = getattr(_wgl, name)
        func.argtypes = argtypes
        func.restype = rtype
        return func
    except AttributeError, e:
        raise ImportError(e)

WGL_SWAP_MAIN_PLANE = 1

wglGetProcAddress = _get_function('wglGetProcAddress', [_ctypes.c_char_p], _ctypes.c_long)
wglCreateContext = _get_function('wglCreateContext', [_ctypes.c_long], _ctypes.c_long)
wglMakeCurrent = _get_function('wglMakeCurrent', [_ctypes.c_long, _ctypes.c_long], _ctypes.c_int)
wglSwapLayerBuffers = _get_function('wglSwapLayerBuffers', [_ctypes.c_long, _ctypes.c_uint], _ctypes.c_int)

