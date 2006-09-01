
"""EXT_fog_coord
http://oss.sgi.com/projects/ogl-sample/registry/EXT/fog_coord.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_FOG_COORDINATE_SOURCE_EXT = 0x8450
GL_FOG_COORDINATE_EXT = 0x8451
GL_FRAGMENT_DEPTH_EXT = 0x8452
GL_CURRENT_FOG_COORDINATE_EXT = 0x8453
GL_FOG_COORDINATE_ARRAY_TYPE_EXT = 0x8454
GL_FOG_COORDINATE_ARRAY_STRIDE_EXT = 0x8455
GL_FOG_COORDINATE_ARRAY_POINTER_EXT = 0x8456
GL_FOG_COORDINATE_ARRAY_EXT = 0x8457
glFogCoordfEXT = _get_function('glFogCoordfEXT', [_ctypes.c_float], None)
glFogCoordfvEXT = _get_function('glFogCoordfvEXT', [_ctypes.POINTER(_ctypes.c_float)], None)
glFogCoorddEXT = _get_function('glFogCoorddEXT', [_ctypes.c_double], None)
glFogCoorddvEXT = _get_function('glFogCoorddvEXT', [_ctypes.POINTER(_ctypes.c_double)], None)
glFogCoordPointerEXT = _get_function('glFogCoordPointerEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
