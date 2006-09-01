
"""ARB_depth_texture
http://oss.sgi.com/projects/ogl-sample/registry/ARB/depth_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_DEPTH_COMPONENT16_ARB = 0x81A5
GL_DEPTH_COMPONENT24_ARB = 0x81A6
GL_DEPTH_COMPONENT32_ARB = 0x81A7
GL_TEXTURE_DEPTH_SIZE_ARB = 0x884A
GL_DEPTH_TEXTURE_MODE_ARB = 0x884B
