
"""EXT_secondary_color
http://oss.sgi.com/projects/ogl-sample/registry/EXT/secondary_color.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_COLOR_SUM_EXT = 0x8458
GL_CURRENT_SECONDARY_COLOR_EXT = 0x8459
GL_SECONDARY_COLOR_ARRAY_SIZE_EXT = 0x845A
GL_SECONDARY_COLOR_ARRAY_TYPE_EXT = 0x845B
GL_SECONDARY_COLOR_ARRAY_STRIDE_EXT = 0x845C
GL_SECONDARY_COLOR_ARRAY_POINTER_EXT = 0x845D
GL_SECONDARY_COLOR_ARRAY_EXT = 0x845E
glSecondaryColor3bEXT = _get_function('glSecondaryColor3bEXT', [_ctypes.c_byte, _ctypes.c_byte, _ctypes.c_byte], None)
glSecondaryColor3bvEXT = _get_function('glSecondaryColor3bvEXT', [_ctypes.POINTER(_ctypes.c_byte)], None)
glSecondaryColor3dEXT = _get_function('glSecondaryColor3dEXT', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glSecondaryColor3dvEXT = _get_function('glSecondaryColor3dvEXT', [_ctypes.POINTER(_ctypes.c_double)], None)
glSecondaryColor3fEXT = _get_function('glSecondaryColor3fEXT', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glSecondaryColor3fvEXT = _get_function('glSecondaryColor3fvEXT', [_ctypes.POINTER(_ctypes.c_float)], None)
glSecondaryColor3iEXT = _get_function('glSecondaryColor3iEXT', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glSecondaryColor3ivEXT = _get_function('glSecondaryColor3ivEXT', [_ctypes.POINTER(_ctypes.c_int)], None)
glSecondaryColor3sEXT = _get_function('glSecondaryColor3sEXT', [_ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glSecondaryColor3svEXT = _get_function('glSecondaryColor3svEXT', [_ctypes.POINTER(_ctypes.c_short)], None)
glSecondaryColor3ubEXT = _get_function('glSecondaryColor3ubEXT', [_ctypes.c_ubyte, _ctypes.c_ubyte, _ctypes.c_ubyte], None)
glSecondaryColor3ubvEXT = _get_function('glSecondaryColor3ubvEXT', [_ctypes.POINTER(_ctypes.c_ubyte)], None)
glSecondaryColor3uiEXT = _get_function('glSecondaryColor3uiEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glSecondaryColor3uivEXT = _get_function('glSecondaryColor3uivEXT', [_ctypes.POINTER(_ctypes.c_uint)], None)
glSecondaryColor3usEXT = _get_function('glSecondaryColor3usEXT', [_ctypes.c_ushort, _ctypes.c_ushort, _ctypes.c_ushort], None)
glSecondaryColor3usvEXT = _get_function('glSecondaryColor3usvEXT', [_ctypes.POINTER(_ctypes.c_ushort)], None)
glSecondaryColorPointerEXT = _get_function('glSecondaryColorPointerEXT', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
