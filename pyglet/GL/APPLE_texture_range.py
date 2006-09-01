
"""APPLE_texture_range
http://developer.apple.com/opengl/extensions/apple_texture_range.html
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_STORAGE_HINT_APPLE = 0x85BC
GL_STORAGE_PRIVATE_APPLE = 0x85BD
GL_STORAGE_CACHED_APPLE = 0x85BE
GL_STORAGE_SHARED_APPLE = 0x85BF
GL_TEXTURE_RANGE_LENGTH_APPLE = 0x85B7
GL_TEXTURE_RANGE_POINTER_APPLE = 0x85B8
glTextureRangeAPPLE = _get_function('glTextureRangeAPPLE', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glGetTexParameterPointervAPPLE = _get_function('glGetTexParameterPointervAPPLE', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p)], None)
