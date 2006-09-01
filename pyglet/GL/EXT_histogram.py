
"""EXT_histogram
http://oss.sgi.com/projects/ogl-sample/registry/EXT/histogram.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_HISTOGRAM_EXT = 0x8024
GL_PROXY_HISTOGRAM_EXT = 0x8025
GL_HISTOGRAM_WIDTH_EXT = 0x8026
GL_HISTOGRAM_FORMAT_EXT = 0x8027
GL_HISTOGRAM_RED_SIZE_EXT = 0x8028
GL_HISTOGRAM_GREEN_SIZE_EXT = 0x8029
GL_HISTOGRAM_BLUE_SIZE_EXT = 0x802A
GL_HISTOGRAM_ALPHA_SIZE_EXT = 0x802B
GL_HISTOGRAM_LUMINANCE_SIZE_EXT = 0x802C
GL_HISTOGRAM_SINK_EXT = 0x802D
GL_MINMAX_EXT = 0x802E
GL_MINMAX_FORMAT_EXT = 0x802F
GL_MINMAX_SINK_EXT = 0x8030
glGetHistogramEXT = _get_function('glGetHistogramEXT', [_ctypes.c_uint, _ctypes.c_ubyte, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glGetHistogramParameterfvEXT = _get_function('glGetHistogramParameterfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetHistogramParameterivEXT = _get_function('glGetHistogramParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetMinmaxEXT = _get_function('glGetMinmaxEXT', [_ctypes.c_uint, _ctypes.c_ubyte, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glGetMinmaxParameterfvEXT = _get_function('glGetMinmaxParameterfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetMinmaxParameterivEXT = _get_function('glGetMinmaxParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glHistogramEXT = _get_function('glHistogramEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_ubyte], None)
glMinmaxEXT = _get_function('glMinmaxEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_ubyte], None)
glResetHistogramEXT = _get_function('glResetHistogramEXT', [_ctypes.c_uint], None)
glResetMinmaxEXT = _get_function('glResetMinmaxEXT', [_ctypes.c_uint], None)
