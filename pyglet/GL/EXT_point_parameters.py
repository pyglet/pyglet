
"""EXT_point_parameters
http://oss.sgi.com/projects/ogl-sample/registry/EXT/point_parameters.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_POINT_SIZE_MIN_EXT = 0x8126
GL_POINT_SIZE_MAX_EXT = 0x8127
GL_POINT_FADE_THRESHOLD_SIZE_EXT = 0x8128
GL_DISTANCE_ATTENUATION_EXT = 0x8129
glPointParameterfEXT = _get_function('glPointParameterfEXT', [_ctypes.c_uint, _ctypes.c_float], None)
glPointParameterfvEXT = _get_function('glPointParameterfvEXT', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
