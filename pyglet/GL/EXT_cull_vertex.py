
"""EXT_cull_vertex
http://oss.sgi.com/projects/ogl-sample/registry/EXT/cull_vertex.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glCullParameterdvEXT = _get_function('glCullParameterdvEXT', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glCullParameterfvEXT = _get_function('glCullParameterfvEXT', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
