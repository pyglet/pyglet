
"""EXT_index_func
http://oss.sgi.com/projects/ogl-sample/registry/EXT/index_func.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glIndexFuncEXT = _get_function('glIndexFuncEXT', [_ctypes.c_uint, _ctypes.c_float], None)
