
"""EXT_texture_perturb_normal
http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture_perturb_normal.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PERTURB_EXT = 0x85AE
GL_TEXTURE_NORMAL_EXT = 0x85AF
glTextureNormalEXT = _get_function('glTextureNormalEXT', [_ctypes.c_uint], None)
