
"""SGIX_fog_texture
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/fog_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_FOG_SGIX = 0
GL_FOG_PATCHY_FACTOR_SGIX = 0
GL_FRAGMENT_FOG_SGIX = 0
glTextureFogSGIX = _get_function('glTextureFogSGIX', [_ctypes.c_uint], None)
