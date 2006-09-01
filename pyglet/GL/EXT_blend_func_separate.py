
"""EXT_blend_func_separate
http://oss.sgi.com/projects/ogl-sample/registry/EXT/blend_func_separate.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_BLEND_DST_RGB_EXT = 0x80C8
GL_BLEND_SRC_RGB_EXT = 0x80C9
GL_BLEND_DST_ALPHA_EXT = 0x80CA
GL_BLEND_SRC_ALPHA_EXT = 0x80CB
glBlendFuncSeparateEXT = _get_function('glBlendFuncSeparateEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
