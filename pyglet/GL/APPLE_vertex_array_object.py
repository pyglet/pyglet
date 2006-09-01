
"""APPLE_vertex_array_object
http://oss.sgi.com/projects/ogl-sample/registry/APPLE/vertex_array_object.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_VERTEX_ARRAY_BINDING_APPLE = 0x85B5
glBindVertexArrayAPPLE = _get_function('glBindVertexArrayAPPLE', [_ctypes.c_uint], None)
glDeleteVertexArraysAPPLE = _get_function('glDeleteVertexArraysAPPLE', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGenVertexArraysAPPLE = _get_function('glGenVertexArraysAPPLE', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glIsVertexArrayAPPLE = _get_function('glIsVertexArrayAPPLE', [_ctypes.c_uint], _ctypes.c_ubyte)
