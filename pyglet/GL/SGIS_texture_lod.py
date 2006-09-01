
"""SGIS_texture_lod
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/texture_lod.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_MIN_LOD_SGIS = 0x813A
GL_TEXTURE_MAX_LOD_SGIS = 0x813B
GL_TEXTURE_BASE_LEVEL_SGIS = 0x813C
GL_TEXTURE_MAX_LEVEL_SGIS = 0x813D
