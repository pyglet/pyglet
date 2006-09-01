
"""INTEL_parallel_arrays
http://oss.sgi.com/projects/ogl-sample/registry/INTEL/parallel_arrays.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PARALLEL_ARRAYS_INTEL = 0x83F4
GL_VERTEX_ARRAY_PARALLEL_POINTERS_INTEL = 0x83F5
GL_NORMAL_ARRAY_PARALLEL_POINTERS_INTEL = 0x83F6
GL_COLOR_ARRAY_PARALLEL_POINTERS_INTEL = 0x83F7
GL_TEXTURE_COORD_ARRAY_PARALLEL_POINTERS_INTEL = 0x83F8
glColorPointervINTEL = _get_function('glColorPointervINTEL', [_ctypes.c_int, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p)], None)
glNormalPointervINTEL = _get_function('glNormalPointervINTEL', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p)], None)
glTexCoordPointervINTEL = _get_function('glTexCoordPointervINTEL', [_ctypes.c_int, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p)], None)
glVertexPointervINTEL = _get_function('glVertexPointervINTEL', [_ctypes.c_int, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p)], None)
