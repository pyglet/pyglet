
"""NV_pixel_data_range
http://oss.sgi.com/projects/ogl-sample/registry/NV/pixel_data_range.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_WRITE_PIXEL_DATA_RANGE_NV = 0x8878
GL_READ_PIXEL_DATA_RANGE_NV = 0x8879
GL_WRITE_PIXEL_DATA_RANGE_LENGTH_NV = 0x887A
GL_READ_PIXEL_DATA_RANGE_LENGTH_NV = 0x887B
GL_WRITE_PIXEL_DATA_RANGE_POINTER_NV = 0x887C
GL_READ_PIXEL_DATA_RANGE_POINTER_NV = 0x887D
glFlushPixelDataRangeNV = _get_function('glFlushPixelDataRangeNV', [_ctypes.c_uint], None)
glPixelDataRangeNV = _get_function('glPixelDataRangeNV', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
