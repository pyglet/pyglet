
"""NV_vertex_array_range
http://oss.sgi.com/projects/ogl-sample/registry/NV/vertex_array_range.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_VERTEX_ARRAY_RANGE_NV = 0x851D
GL_VERTEX_ARRAY_RANGE_LENGTH_NV = 0x851E
GL_VERTEX_ARRAY_RANGE_VALID_NV = 0x851F
GL_MAX_VERTEX_ARRAY_RANGE_ELEMENT_NV = 0x8520
GL_VERTEX_ARRAY_RANGE_POINTER_NV = 0x8521
glFlushVertexArrayRangeNV = _get_function('glFlushVertexArrayRangeNV', [], None)
glVertexArrayRangeNV = _get_function('glVertexArrayRangeNV', [_ctypes.c_int, _ctypes.c_void_p], None)
