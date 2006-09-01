
"""EXT_pixel_transform
http://oss.sgi.com/projects/ogl-sample/registry/EXT/pixel_transform.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PIXEL_TRANSFORM_2D_EXT = 0x8330
GL_PIXEL_MAG_FILTER_EXT = 0x8331
GL_PIXEL_MIN_FILTER_EXT = 0x8332
GL_PIXEL_CUBIC_WEIGHT_EXT = 0x8333
GL_CUBIC_EXT = 0x8334
GL_AVERAGE_EXT = 0x8335
GL_PIXEL_TRANSFORM_2D_STACK_DEPTH_EXT = 0x8336
GL_MAX_PIXEL_TRANSFORM_2D_STACK_DEPTH_EXT = 0x8337
GL_PIXEL_TRANSFORM_2D_MATRIX_EXT = 0x8338
glGetPixelTransformParameterfvEXT = _get_function('glGetPixelTransformParameterfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetPixelTransformParameterivEXT = _get_function('glGetPixelTransformParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glPixelTransformParameterfEXT = _get_function('glPixelTransformParameterfEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_float], None)
glPixelTransformParameterfvEXT = _get_function('glPixelTransformParameterfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glPixelTransformParameteriEXT = _get_function('glPixelTransformParameteriEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glPixelTransformParameterivEXT = _get_function('glPixelTransformParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
