
"""SGIX_shadow
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/shadow.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_COMPARE_SGIX = 0x819A
GL_TEXTURE_COMPARE_OPERATOR_SGIX = 0x819B
GL_TEXTURE_LEQUAL_R_SGIX = 0x819C
GL_TEXTURE_GEQUAL_R_SGIX = 0x819D
