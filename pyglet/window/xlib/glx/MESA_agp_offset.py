
"""MESA_agp_offset
http://oss.sgi.com/projects/ogl-sample/registry/MESA/agp_offset.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXGetAGPOffsetMESA = _get_function('glXGetAGPOffsetMESA', [_ctypes.c_void_p], _ctypes.c_uint)
