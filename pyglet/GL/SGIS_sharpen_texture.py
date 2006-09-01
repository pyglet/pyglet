
"""SGIS_sharpen_texture
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/sharpen_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glGetSharpenTexFuncSGIS = _get_function('glGetSharpenTexFuncSGIS', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glSharpenTexFuncSGIS = _get_function('glSharpenTexFuncSGIS', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
