
"""SGIS_generate_mipmap
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/generate_mipmap.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_GENERATE_MIPMAP_SGIS = 0x8191
GL_GENERATE_MIPMAP_HINT_SGIS = 0x8192
