#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes as _ctypes
from pyglet.GLU import get_function as _get_function
from pyglet.GLU.VERSION_1_2 import *

gluCheckExtension = _get_function('gluCheckExtension', [_ctypes.c_char_p, _ctypes.c_char_p], _ctypes.c_ubyte)
gluScaleImage = _get_function('gluScaleImage', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_void_p, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_void_p], _ctypes.c_int)
gluBuild1DMipmapLevels = _get_function('gluBuild1DMipmapLevels', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], _ctypes.c_int)
gluBuild2DMipmapLevels = _get_function('gluBuild2DMipmapLevels', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], _ctypes.c_int)
gluBuild3DMipmaps = _get_function('gluBuild3DMipmaps', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], _ctypes.c_int)
gluBuild3DMipmapLevels = _get_function('gluBuild3DMipmapLevels', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], _ctypes.c_int)
gluUnProject4 = _get_function('gluUnProject4', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_int), _ctypes.c_double, _ctypes.c_double, _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double)], _ctypes.c_int)

#gluNurbsCallbackDataEXT = _get_function('gluNurbsCallbackDataEXT', [_ctypes.c_void_p, _ctypes.c_void_p], None)
