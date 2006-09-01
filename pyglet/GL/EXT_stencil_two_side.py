
"""EXT_stencil_two_side
http://oss.sgi.com/projects/ogl-sample/registry/EXT/stencil_two_side.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_STENCIL_TEST_TWO_SIDE_EXT = 0x8910
GL_ACTIVE_STENCIL_FACE_EXT = 0x8911
glActiveStencilFaceEXT = _get_function('glActiveStencilFaceEXT', [_ctypes.c_uint], None)
