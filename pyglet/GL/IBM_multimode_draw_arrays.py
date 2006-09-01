
"""IBM_multimode_draw_arrays
http://oss.sgi.com/projects/ogl-sample/registry/IBM/multimode_draw_arrays.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glMultiModeDrawArraysIBM = _get_function('glMultiModeDrawArraysIBM', [_ctypes.POINTER(_ctypes.c_uint), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.c_int, _ctypes.c_int], None)
glMultiModeDrawElementsIBM = _get_function('glMultiModeDrawElementsIBM', [_ctypes.POINTER(_ctypes.c_uint), _ctypes.POINTER(_ctypes.c_int), _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int, _ctypes.c_int], None)
