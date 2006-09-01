
"""SGIS_detail_texture
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/detail_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glDetailTexFuncSGIS = _get_function('glDetailTexFuncSGIS', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glGetDetailTexFuncSGIS = _get_function('glGetDetailTexFuncSGIS', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
