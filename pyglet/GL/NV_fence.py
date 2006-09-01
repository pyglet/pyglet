
"""NV_fence
http://oss.sgi.com/projects/ogl-sample/registry/NV/fence.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_ALL_COMPLETED_NV = 0x84F2
GL_FENCE_STATUS_NV = 0x84F3
GL_FENCE_CONDITION_NV = 0x84F4
glDeleteFencesNV = _get_function('glDeleteFencesNV', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glFinishFenceNV = _get_function('glFinishFenceNV', [_ctypes.c_uint], None)
glGenFencesNV = _get_function('glGenFencesNV', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGetFenceivNV = _get_function('glGetFenceivNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glIsFenceNV = _get_function('glIsFenceNV', [_ctypes.c_uint], _ctypes.c_ubyte)
glSetFenceNV = _get_function('glSetFenceNV', [_ctypes.c_uint, _ctypes.c_uint], None)
glTestFenceNV = _get_function('glTestFenceNV', [_ctypes.c_uint], _ctypes.c_ubyte)
