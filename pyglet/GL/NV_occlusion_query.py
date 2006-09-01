
"""NV_occlusion_query
http://oss.sgi.com/projects/ogl-sample/registry/NV/occlusion_query.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PIXEL_COUNTER_BITS_NV = 0x8864
GL_CURRENT_OCCLUSION_QUERY_ID_NV = 0x8865
GL_PIXEL_COUNT_NV = 0x8866
GL_PIXEL_COUNT_AVAILABLE_NV = 0x8867
glBeginOcclusionQueryNV = _get_function('glBeginOcclusionQueryNV', [_ctypes.c_uint], None)
glDeleteOcclusionQueriesNV = _get_function('glDeleteOcclusionQueriesNV', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glEndOcclusionQueryNV = _get_function('glEndOcclusionQueryNV', [], None)
glGenOcclusionQueriesNV = _get_function('glGenOcclusionQueriesNV', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGetOcclusionQueryivNV = _get_function('glGetOcclusionQueryivNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetOcclusionQueryuivNV = _get_function('glGetOcclusionQueryuivNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_uint)], None)
glIsOcclusionQueryNV = _get_function('glIsOcclusionQueryNV', [_ctypes.c_uint], _ctypes.c_ubyte)
