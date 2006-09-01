
"""EXT_color_subtable
http://oss.sgi.com/projects/ogl-sample/registry/EXT/color_subtable.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glColorSubTableEXT = _get_function('glColorSubTableEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glCopyColorSubTableEXT = _get_function('glCopyColorSubTableEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
