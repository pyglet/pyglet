
"""EXT_subtexture
http://oss.sgi.com/projects/ogl-sample/registry/EXT/subtexture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glTexSubImage1DEXT = _get_function('glTexSubImage1DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glTexSubImage2DEXT = _get_function('glTexSubImage2DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glTexSubImage3DEXT = _get_function('glTexSubImage3DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
