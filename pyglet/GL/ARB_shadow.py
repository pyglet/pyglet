
"""ARB_shadow
http://oss.sgi.com/projects/ogl-sample/registry/ARB/shadow.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_COMPARE_MODE_ARB = 0x884C
GL_TEXTURE_COMPARE_FUNC_ARB = 0x884D
GL_COMPARE_R_TO_TEXTURE_ARB = 0x884E
