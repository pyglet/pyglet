#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes as _ctypes
from pyglet.window.carbon.agl.VERSION_10_2 import *
from pyglet.window.carbon.agl.VERSION_10_2 import _get_function

aglCreatePBuffer = _get_function('aglCreatePBuffer', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_long, _ctypes.POINTER(_ctypes.c_void_p)], _ctypes.c_ubyte)
aglDestroyPBuffer = _get_function('aglDestroyPBuffer', [_ctypes.c_void_p], _ctypes.c_ubyte)
aglDescribePBuffer = _get_function('aglDescribePBuffer', [_ctypes.c_void_p, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_uint), _ctypes.POINTER(_ctypes.c_uint), _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglTexImagePBuffer = _get_function('aglTexImagePBuffer', [_ctypes.c_void_p, _ctypes.c_void_p, _ctypes.c_int], _ctypes.c_ubyte)
aglSetPBuffer = _get_function('aglSetPBuffer', [_ctypes.c_void_p, _ctypes.c_void_p, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], _ctypes.c_ubyte)
aglGetPBuffer = _get_function('aglGetPBuffer', [_ctypes.c_void_p, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
