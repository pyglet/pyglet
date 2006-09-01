
"""EXT_multi_draw_arrays
http://oss.sgi.com/projects/ogl-sample/registry/EXT/multi_draw_arrays.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glMultiDrawArraysEXT = _get_function('glMultiDrawArraysEXT', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.c_int], None)
glMultiDrawElementsEXT = _get_function('glMultiDrawElementsEXT', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int), _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
