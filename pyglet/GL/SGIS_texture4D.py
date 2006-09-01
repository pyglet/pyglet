
"""SGIS_texture4D
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/texture4D.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glTexImage4DSGIS = _get_function('glTexImage4DSGIS', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glTexSubImage4DSGIS = _get_function('glTexSubImage4DSGIS', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
