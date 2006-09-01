
"""SGIX_texture_coordinate_clamp
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/texture_coordinate_clamp.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_MAX_CLAMP_S_SGIX = 0x8369
GL_TEXTURE_MAX_CLAMP_T_SGIX = 0x836A
GL_TEXTURE_MAX_CLAMP_R_SGIX = 0x836B
