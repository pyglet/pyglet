
"""NV_point_sprite
http://oss.sgi.com/projects/ogl-sample/registry/NV/point_sprite.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_POINT_SPRITE_NV = 0x8861
GL_COORD_REPLACE_NV = 0x8862
GL_POINT_SPRITE_R_MODE_NV = 0x8863
glPointParameteriNV = _get_function('glPointParameteriNV', [_ctypes.c_uint, _ctypes.c_int], None)
glPointParameterivNV = _get_function('glPointParameterivNV', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
