
"""EXT_blend_equation_separate
http://oss.sgi.com/projects/ogl-sample/registry/EXT/blend_equation_separate.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_BLEND_EQUATION_RGB_EXT = 0x8009
GL_BLEND_EQUATION_ALPHA_EXT = 0x883D
glBlendEquationSeparateEXT = _get_function('glBlendEquationSeparateEXT', [_ctypes.c_uint, _ctypes.c_uint], None)
