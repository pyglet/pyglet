
"""EXT_compiled_vertex_array
http://oss.sgi.com/projects/ogl-sample/registry/EXT/compiled_vertex_array.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glLockArraysEXT = _get_function('glLockArraysEXT', [_ctypes.c_int, _ctypes.c_int], None)
glUnlockArraysEXT = _get_function('glUnlockArraysEXT', [], None)
