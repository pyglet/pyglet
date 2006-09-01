
"""SGI_color_table
http://oss.sgi.com/projects/ogl-sample/registry/SGI/color_table.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_COLOR_TABLE_SGI = 0x80D0
GL_POST_CONVOLUTION_COLOR_TABLE_SGI = 0x80D1
GL_POST_COLOR_MATRIX_COLOR_TABLE_SGI = 0x80D2
GL_PROXY_COLOR_TABLE_SGI = 0x80D3
GL_PROXY_POST_CONVOLUTION_COLOR_TABLE_SGI = 0x80D4
GL_PROXY_POST_COLOR_MATRIX_COLOR_TABLE_SGI = 0x80D5
GL_COLOR_TABLE_SCALE_SGI = 0x80D6
GL_COLOR_TABLE_BIAS_SGI = 0x80D7
GL_COLOR_TABLE_FORMAT_SGI = 0x80D8
GL_COLOR_TABLE_WIDTH_SGI = 0x80D9
GL_COLOR_TABLE_RED_SIZE_SGI = 0x80DA
GL_COLOR_TABLE_GREEN_SIZE_SGI = 0x80DB
GL_COLOR_TABLE_BLUE_SIZE_SGI = 0x80DC
GL_COLOR_TABLE_ALPHA_SIZE_SGI = 0x80DD
GL_COLOR_TABLE_LUMINANCE_SIZE_SGI = 0x80DE
GL_COLOR_TABLE_INTENSITY_SIZE_SGI = 0x80DF
glColorTableParameterfvSGI = _get_function('glColorTableParameterfvSGI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glColorTableParameterivSGI = _get_function('glColorTableParameterivSGI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glColorTableSGI = _get_function('glColorTableSGI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glCopyColorTableSGI = _get_function('glCopyColorTableSGI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glGetColorTableParameterfvSGI = _get_function('glGetColorTableParameterfvSGI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetColorTableParameterivSGI = _get_function('glGetColorTableParameterivSGI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetColorTableSGI = _get_function('glGetColorTableSGI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
