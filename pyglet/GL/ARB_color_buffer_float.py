
"""ARB_color_buffer_float
http://oss.sgi.com/projects/ogl-sample/registry/ARB/color_buffer_float.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_RGBA_FLOAT_MODE_ARB = 0x8820
GL_CLAMP_VERTEX_COLOR_ARB = 0x891A
GL_CLAMP_FRAGMENT_COLOR_ARB = 0x891B
GL_CLAMP_READ_COLOR_ARB = 0x891C
GL_FIXED_ONLY_ARB = 0x891D
glClampColorARB = _get_function('glClampColorARB', [_ctypes.c_uint, _ctypes.c_uint], None)
