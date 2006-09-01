
"""SGIX_sprite
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/sprite.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glSpriteParameterfSGIX = _get_function('glSpriteParameterfSGIX', [_ctypes.c_uint, _ctypes.c_float], None)
glSpriteParameterfvSGIX = _get_function('glSpriteParameterfvSGIX', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glSpriteParameteriSGIX = _get_function('glSpriteParameteriSGIX', [_ctypes.c_uint, _ctypes.c_int], None)
glSpriteParameterivSGIX = _get_function('glSpriteParameterivSGIX', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
