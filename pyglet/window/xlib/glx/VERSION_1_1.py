#!/usr/bin/env python

'''VERSION_1_1
/usr/include/GL/glx.h
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.window.xlib.glx.VERSION_1_0 import *
import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t

glXGetClientString = _get_function('glXGetClientString', [_ctypes.POINTER(Display), _ctypes.c_int], _ctypes.c_char_p)
glXQueryServerString = _get_function('glXQueryServerString', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.c_int], _ctypes.c_char_p)
glXQueryExtensionsString = _get_function('glXQueryExtensionsString', [_ctypes.POINTER(Display), _ctypes.c_int], _ctypes.c_char_p)
