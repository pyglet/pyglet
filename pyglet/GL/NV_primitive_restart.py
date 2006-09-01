
"""NV_primitive_restart
http://oss.sgi.com/projects/ogl-sample/registry/NV/primitive_restart.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PRIMITIVE_RESTART_NV = 0x8558
GL_PRIMITIVE_RESTART_INDEX_NV = 0x8559
glPrimitiveRestartIndexNV = _get_function('glPrimitiveRestartIndexNV', [_ctypes.c_uint], None)
glPrimitiveRestartNV = _get_function('glPrimitiveRestartNV', [], None)
