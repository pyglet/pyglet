
"""ARB_occlusion_query
http://oss.sgi.com/projects/ogl-sample/registry/ARB/occlusion_query.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_QUERY_COUNTER_BITS_ARB = 0x8864
GL_CURRENT_QUERY_ARB = 0x8865
GL_QUERY_RESULT_ARB = 0x8866
GL_QUERY_RESULT_AVAILABLE_ARB = 0x8867
GL_SAMPLES_PASSED_ARB = 0x8914
glBeginQueryARB = _get_function('glBeginQueryARB', [_ctypes.c_uint, _ctypes.c_uint], None)
glDeleteQueriesARB = _get_function('glDeleteQueriesARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glEndQueryARB = _get_function('glEndQueryARB', [_ctypes.c_uint], None)
glGenQueriesARB = _get_function('glGenQueriesARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGetQueryObjectivARB = _get_function('glGetQueryObjectivARB', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetQueryObjectuivARB = _get_function('glGetQueryObjectuivARB', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_uint)], None)
glGetQueryivARB = _get_function('glGetQueryivARB', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glIsQueryARB = _get_function('glIsQueryARB', [_ctypes.c_uint], _ctypes.c_ubyte)
