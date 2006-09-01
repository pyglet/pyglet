
"""EXT_blend_color
http://oss.sgi.com/projects/ogl-sample/registry/EXT/blend_color.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_CONSTANT_COLOR_EXT = 0x8001
GL_ONE_MINUS_CONSTANT_COLOR_EXT = 0x8002
GL_CONSTANT_ALPHA_EXT = 0x8003
GL_ONE_MINUS_CONSTANT_ALPHA_EXT = 0x8004
GL_BLEND_COLOR_EXT = 0x8005
glBlendColorEXT = _get_function('glBlendColorEXT', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
