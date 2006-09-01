
"""SGIX_async
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/async.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_ASYNC_MARKER_SGIX = 0x8329
glAsyncMarkerSGIX = _get_function('glAsyncMarkerSGIX', [_ctypes.c_uint], None)
glDeleteAsyncMarkersSGIX = _get_function('glDeleteAsyncMarkersSGIX', [_ctypes.c_uint, _ctypes.c_int], None)
glFinishAsyncSGIX = _get_function('glFinishAsyncSGIX', [_ctypes.POINTER(_ctypes.c_uint)], _ctypes.c_int)
glGenAsyncMarkersSGIX = _get_function('glGenAsyncMarkersSGIX', [_ctypes.c_int], _ctypes.c_uint)
glIsAsyncMarkerSGIX = _get_function('glIsAsyncMarkerSGIX', [_ctypes.c_uint], _ctypes.c_ubyte)
glPollAsyncSGIX = _get_function('glPollAsyncSGIX', [_ctypes.POINTER(_ctypes.c_uint)], _ctypes.c_int)
