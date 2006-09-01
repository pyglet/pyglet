
"""VERSION_1_4
GL_GENERATE_MIPMAP 0x8191
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
from pyglet.GL.VERSION_1_3 import *
GL_GENERATE_MIPMAP_HINT = 0x8192
GL_DEPTH_COMPONENT16 = 0x81A5
GL_DEPTH_COMPONENT24 = 0x81A6
GL_DEPTH_COMPONENT32 = 0x81A7
GL_TEXTURE_DEPTH_SIZE = 0x884A
GL_DEPTH_TEXTURE_MODE = 0x884B
GL_TEXTURE_COMPARE_MODE = 0x884C
GL_TEXTURE_COMPARE_FUNC = 0x884D
GL_COMPARE_R_TO_TEXTURE = 0x884E
GL_FOG_COORDINATE_SOURCE = 0x8450
GL_FOG_COORDINATE = 0x8451
GL_FRAGMENT_DEPTH = 0x8452
GL_CURRENT_FOG_COORDINATE = 0x8453
GL_FOG_COORDINATE_ARRAY_TYPE = 0x8454
GL_FOG_COORDINATE_ARRAY_STRIDE = 0x8455
GL_FOG_COORDINATE_ARRAY_POINTER = 0x8456
GL_FOG_COORDINATE_ARRAY = 0x8457
GL_POINT_SIZE_MIN = 0x8126
GL_POINT_SIZE_MAX = 0x8127
GL_POINT_FADE_THRESHOLD_SIZE = 0x8128
GL_POINT_DISTANCE_ATTENUATION = 0x8129
GL_COLOR_SUM = 0x8458
GL_CURRENT_SECONDARY_COLOR = 0x8459
GL_SECONDARY_COLOR_ARRAY_SIZE = 0x845A
GL_SECONDARY_COLOR_ARRAY_TYPE = 0x845B
GL_SECONDARY_COLOR_ARRAY_STRIDE = 0x845C
GL_SECONDARY_COLOR_ARRAY_POINTER = 0x845D
GL_SECONDARY_COLOR_ARRAY = 0x845E
GL_BLEND_DST_RGB = 0x80C8
GL_BLEND_SRC_RGB = 0x80C9
GL_BLEND_DST_ALPHA = 0x80CA
GL_BLEND_SRC_ALPHA = 0x80CB
GL_INCR_WRAP = 0x8507
GL_DECR_WRAP = 0x8508
GL_TEXTURE_FILTER_CONTROL = 0x8500
GL_TEXTURE_LOD_BIAS = 0x8501
GL_MAX_TEXTURE_LOD_BIAS = 0x84FD
GL_MIRRORED_REPEAT = 0x8370
glBlendEquation = _get_function('glBlendEquation', [_ctypes.c_uint], None)
glBlendColor = _get_function('glBlendColor', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glFogCoordf = _get_function('glFogCoordf', [_ctypes.c_float], None)
glFogCoordfv = _get_function('glFogCoordfv', [_ctypes.POINTER(_ctypes.c_float)], None)
glFogCoordd = _get_function('glFogCoordd', [_ctypes.c_double], None)
glFogCoorddv = _get_function('glFogCoorddv', [_ctypes.POINTER(_ctypes.c_double)], None)
glFogCoordPointer = _get_function('glFogCoordPointer', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glMultiDrawArrays = _get_function('glMultiDrawArrays', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.c_int], None)
glMultiDrawElements = _get_function('glMultiDrawElements', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int), _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
glPointParameterf = _get_function('glPointParameterf', [_ctypes.c_uint, _ctypes.c_float], None)
glPointParameterfv = _get_function('glPointParameterfv', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glSecondaryColor3b = _get_function('glSecondaryColor3b', [_ctypes.c_byte, _ctypes.c_byte, _ctypes.c_byte], None)
glSecondaryColor3bv = _get_function('glSecondaryColor3bv', [_ctypes.POINTER(_ctypes.c_byte)], None)
glSecondaryColor3d = _get_function('glSecondaryColor3d', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glSecondaryColor3dv = _get_function('glSecondaryColor3dv', [_ctypes.POINTER(_ctypes.c_double)], None)
glSecondaryColor3f = _get_function('glSecondaryColor3f', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glSecondaryColor3fv = _get_function('glSecondaryColor3fv', [_ctypes.POINTER(_ctypes.c_float)], None)
glSecondaryColor3i = _get_function('glSecondaryColor3i', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glSecondaryColor3iv = _get_function('glSecondaryColor3iv', [_ctypes.POINTER(_ctypes.c_int)], None)
glSecondaryColor3s = _get_function('glSecondaryColor3s', [_ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glSecondaryColor3sv = _get_function('glSecondaryColor3sv', [_ctypes.POINTER(_ctypes.c_short)], None)
glSecondaryColor3ub = _get_function('glSecondaryColor3ub', [_ctypes.c_ubyte, _ctypes.c_ubyte, _ctypes.c_ubyte], None)
glSecondaryColor3ubv = _get_function('glSecondaryColor3ubv', [_ctypes.POINTER(_ctypes.c_ubyte)], None)
glSecondaryColor3ui = _get_function('glSecondaryColor3ui', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glSecondaryColor3uiv = _get_function('glSecondaryColor3uiv', [_ctypes.POINTER(_ctypes.c_uint)], None)
glSecondaryColor3us = _get_function('glSecondaryColor3us', [_ctypes.c_ushort, _ctypes.c_ushort, _ctypes.c_ushort], None)
glSecondaryColor3usv = _get_function('glSecondaryColor3usv', [_ctypes.POINTER(_ctypes.c_ushort)], None)
glSecondaryColorPointer = _get_function('glSecondaryColorPointer', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glBlendFuncSeparate = _get_function('glBlendFuncSeparate', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glWindowPos2d = _get_function('glWindowPos2d', [_ctypes.c_double, _ctypes.c_double], None)
glWindowPos2f = _get_function('glWindowPos2f', [_ctypes.c_float, _ctypes.c_float], None)
glWindowPos2i = _get_function('glWindowPos2i', [_ctypes.c_int, _ctypes.c_int], None)
glWindowPos2s = _get_function('glWindowPos2s', [_ctypes.c_short, _ctypes.c_short], None)
glWindowPos2dv = _get_function('glWindowPos2dv', [_ctypes.POINTER(_ctypes.c_double)], None)
glWindowPos2fv = _get_function('glWindowPos2fv', [_ctypes.POINTER(_ctypes.c_float)], None)
glWindowPos2iv = _get_function('glWindowPos2iv', [_ctypes.POINTER(_ctypes.c_int)], None)
glWindowPos2sv = _get_function('glWindowPos2sv', [_ctypes.POINTER(_ctypes.c_short)], None)
glWindowPos3d = _get_function('glWindowPos3d', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glWindowPos3f = _get_function('glWindowPos3f', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glWindowPos3i = _get_function('glWindowPos3i', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glWindowPos3s = _get_function('glWindowPos3s', [_ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glWindowPos3dv = _get_function('glWindowPos3dv', [_ctypes.POINTER(_ctypes.c_double)], None)
glWindowPos3fv = _get_function('glWindowPos3fv', [_ctypes.POINTER(_ctypes.c_float)], None)
glWindowPos3iv = _get_function('glWindowPos3iv', [_ctypes.POINTER(_ctypes.c_int)], None)
glWindowPos3sv = _get_function('glWindowPos3sv', [_ctypes.POINTER(_ctypes.c_short)], None)
