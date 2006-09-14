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

wglGetProcAddress = _get_function('wglGetProcAddress', [_ctypes.c_char_p], _ctypes.c_long)
