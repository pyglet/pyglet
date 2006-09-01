
"""EXT_blend_minmax
http://oss.sgi.com/projects/ogl-sample/registry/EXT/blend_minmax.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_FUNC_ADD_EXT = 0x8006
GL_MIN_EXT = 0x8007
GL_MAX_EXT = 0x8008
GL_BLEND_EQUATION_EXT = 0x8009
glBlendEquationEXT = _get_function('glBlendEquationEXT', [_ctypes.c_uint], None)
