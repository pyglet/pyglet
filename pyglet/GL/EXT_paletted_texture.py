
"""EXT_paletted_texture
http://oss.sgi.com/projects/ogl-sample/registry/EXT/paletted_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_1D = 0x0DE0
GL_TEXTURE_2D = 0x0DE1
GL_PROXY_TEXTURE_1D = 0x8063
GL_PROXY_TEXTURE_2D = 0x8064
GL_TEXTURE_3D_EXT = 0x806F
GL_PROXY_TEXTURE_3D_EXT = 0x8070
GL_COLOR_TABLE_FORMAT_EXT = 0x80D8
GL_COLOR_TABLE_WIDTH_EXT = 0x80D9
GL_COLOR_TABLE_RED_SIZE_EXT = 0x80DA
GL_COLOR_TABLE_GREEN_SIZE_EXT = 0x80DB
GL_COLOR_TABLE_BLUE_SIZE_EXT = 0x80DC
GL_COLOR_TABLE_ALPHA_SIZE_EXT = 0x80DD
GL_COLOR_TABLE_LUMINANCE_SIZE_EXT = 0x80DE
GL_COLOR_TABLE_INTENSITY_SIZE_EXT = 0x80DF
GL_COLOR_INDEX1_EXT = 0x80E2
GL_COLOR_INDEX2_EXT = 0x80E3
GL_COLOR_INDEX4_EXT = 0x80E4
GL_COLOR_INDEX8_EXT = 0x80E5
GL_COLOR_INDEX12_EXT = 0x80E6
GL_COLOR_INDEX16_EXT = 0x80E7
GL_TEXTURE_INDEX_SIZE_EXT = 0x80ED
GL_TEXTURE_CUBE_MAP_ARB = 0x8513
GL_PROXY_TEXTURE_CUBE_MAP_ARB = 0x851B
glColorTableEXT = _get_function('glColorTableEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glGetColorTableEXT = _get_function('glGetColorTableEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glGetColorTableParameterfvEXT = _get_function('glGetColorTableParameterfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetColorTableParameterivEXT = _get_function('glGetColorTableParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
