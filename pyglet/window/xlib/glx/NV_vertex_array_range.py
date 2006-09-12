
"""NV_vertex_array_range
http://oss.sgi.com/projects/ogl-sample/registry/NV/vertex_array_range.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXAllocateMemoryNV = _get_function('glXAllocateMemoryNV', [_ctypes.c_int, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], _ctypes.c_void_p)
glXFreeMemoryNV = _get_function('glXFreeMemoryNV', [_ctypes.c_void_p], None)
