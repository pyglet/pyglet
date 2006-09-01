
"""SGIS_fog_function
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/fog_func.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glFogFuncSGIS = _get_function('glFogFuncSGIS', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glGetFogFuncSGIS = _get_function('glGetFogFuncSGIS', [_ctypes.POINTER(_ctypes.c_float)], None)
