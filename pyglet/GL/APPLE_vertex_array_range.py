
"""APPLE_vertex_array_range
http://oss.sgi.com/projects/ogl-sample/registry/APPLE/vertex_array_range.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_VERTEX_ARRAY_RANGE_APPLE = 0x851D
GL_VERTEX_ARRAY_RANGE_LENGTH_APPLE = 0x851E
GL_VERTEX_ARRAY_STORAGE_HINT_APPLE = 0x851F
GL_MAX_VERTEX_ARRAY_RANGE_ELEMENT_APPLE = 0x8520
GL_VERTEX_ARRAY_RANGE_POINTER_APPLE = 0x8521
GL_STORAGE_CACHED_APPLE = 0x85BE
GL_STORAGE_SHARED_APPLE = 0x85BF
glFlushVertexArrayRangeAPPLE = _get_function('glFlushVertexArrayRangeAPPLE', [_ctypes.c_int, _ctypes.c_void_p], None)
glVertexArrayParameteriAPPLE = _get_function('glVertexArrayParameteriAPPLE', [_ctypes.c_uint, _ctypes.c_int], None)
glVertexArrayRangeAPPLE = _get_function('glVertexArrayRangeAPPLE', [_ctypes.c_int, _ctypes.c_void_p], None)
