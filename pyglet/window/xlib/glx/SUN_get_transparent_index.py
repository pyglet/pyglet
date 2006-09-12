
"""SUN_get_transparent_index
http://oss.sgi.com/projects/ogl-sample/registry/SUN/get_transparent_index.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXGetTransparentIndexSUN = _get_function('glXGetTransparentIndexSUN', [_ctypes.POINTER(Display), _ctypes.c_ulong, _ctypes.c_ulong, _ctypes.POINTER(_ctypes.c_uint)], Status)
