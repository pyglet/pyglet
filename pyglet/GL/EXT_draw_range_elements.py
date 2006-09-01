
"""EXT_draw_range_elements
http://oss.sgi.com/projects/ogl-sample/registry/EXT/draw_range_elements.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MAX_ELEMENTS_VERTICES = 0x80E8
GL_MAX_ELEMENTS_INDICES = 0x80E9
glDrawRangeElementsEXT = _get_function('glDrawRangeElementsEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_void_p], None)
