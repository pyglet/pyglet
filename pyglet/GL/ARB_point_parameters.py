
"""ARB_point_parameters
http://oss.sgi.com/projects/ogl-sample/registry/ARB/point_parameters.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_POINT_SIZE_MIN_ARB = 0x8126
GL_POINT_SIZE_MAX_ARB = 0x8127
GL_POINT_FADE_THRESHOLD_SIZE_ARB = 0x8128
GL_POINT_DISTANCE_ATTENUATION_ARB = 0x8129
glPointParameterfARB = _get_function('glPointParameterfARB', [_ctypes.c_uint, _ctypes.c_float], None)
glPointParameterfvARB = _get_function('glPointParameterfvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
