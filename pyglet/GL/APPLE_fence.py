
"""APPLE_fence
http://oss.sgi.com/projects/ogl-sample/registry/APPLE/fence.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_DRAW_PIXELS_APPLE = 0x8A0A
GL_FENCE_APPLE = 0x8A0B
glDeleteFencesAPPLE = _get_function('glDeleteFencesAPPLE', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glFinishFenceAPPLE = _get_function('glFinishFenceAPPLE', [_ctypes.c_uint], None)
glFinishObjectAPPLE = _get_function('glFinishObjectAPPLE', [_ctypes.c_uint, _ctypes.c_int], None)
glGenFencesAPPLE = _get_function('glGenFencesAPPLE', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glIsFenceAPPLE = _get_function('glIsFenceAPPLE', [_ctypes.c_uint], _ctypes.c_ubyte)
glSetFenceAPPLE = _get_function('glSetFenceAPPLE', [_ctypes.c_uint], None)
glTestFenceAPPLE = _get_function('glTestFenceAPPLE', [_ctypes.c_uint], _ctypes.c_ubyte)
glTestObjectAPPLE = _get_function('glTestObjectAPPLE', [_ctypes.c_uint, _ctypes.c_uint], _ctypes.c_ubyte)
