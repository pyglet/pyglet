
"""NV_register_combiners2
http://oss.sgi.com/projects/ogl-sample/registry/NV/register_combiners2.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PER_STAGE_CONSTANTS_NV = 0x8535
glCombinerStageParameterfvNV = _get_function('glCombinerStageParameterfvNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetCombinerStageParameterfvNV = _get_function('glGetCombinerStageParameterfvNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
