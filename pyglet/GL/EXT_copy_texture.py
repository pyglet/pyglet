
"""EXT_copy_texture
http://oss.sgi.com/projects/ogl-sample/registry/EXT/copy_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glCopyTexImage1DEXT = _get_function('glCopyTexImage1DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glCopyTexImage2DEXT = _get_function('glCopyTexImage2DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glCopyTexSubImage1DEXT = _get_function('glCopyTexSubImage1DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glCopyTexSubImage2DEXT = _get_function('glCopyTexSubImage2DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glCopyTexSubImage3DEXT = _get_function('glCopyTexSubImage3DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
