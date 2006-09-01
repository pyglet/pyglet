
"""SUNX_constant_data
http://oss.sgi.com/projects/ogl-sample/registry/SUNX/constant_data.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_UNPACK_CONSTANT_DATA_SUNX = 0x81D5
GL_TEXTURE_CONSTANT_DATA_SUNX = 0x81D6
glFinishTextureSUNX = _get_function('glFinishTextureSUNX', [], None)
