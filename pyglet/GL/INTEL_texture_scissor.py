
"""INTEL_texture_scissor
http://oss.sgi.com/projects/ogl-sample/registry/INTEL/texture_scissor.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glTexScissorFuncINTEL = _get_function('glTexScissorFuncINTEL', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glTexScissorINTEL = _get_function('glTexScissorINTEL', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float], None)
