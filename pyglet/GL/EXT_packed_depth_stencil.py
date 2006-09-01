
"""EXT_packed_depth_stencil
http://oss.sgi.com/projects/ogl-sample/registry/EXT/packed_depth_stencil.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_DEPTH_STENCIL_EXT = 0x84F9
GL_UNSIGNED_INT_24_8_EXT = 0x84FA
GL_DEPTH24_STENCIL8_EXT = 0x88F0
GL_TEXTURE_STENCIL_SIZE_EXT = 0x88F1
