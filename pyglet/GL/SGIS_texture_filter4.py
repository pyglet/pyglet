
"""SGIS_texture_filter4
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/texture_filter4.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glGetTexFilterFuncSGIS = _get_function('glGetTexFilterFuncSGIS', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glTexFilterFuncSGIS = _get_function('glTexFilterFuncSGIS', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
