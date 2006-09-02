
"""EXT_texture_object
http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture_object.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE_PRIORITY_EXT = 0x8066
GL_TEXTURE_RESIDENT_EXT = 0x8067
GL_TEXTURE_1D_BINDING_EXT = 0x8068
GL_TEXTURE_2D_BINDING_EXT = 0x8069
GL_TEXTURE_3D_BINDING_EXT = 0x806A
glAreTexturesResidentEXT = _get_function('glAreTexturesResidentEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint), _ctypes.c_char_p], _ctypes.c_ubyte)
glBindTextureEXT = _get_function('glBindTextureEXT', [_ctypes.c_uint, _ctypes.c_uint], None)
glDeleteTexturesEXT = _get_function('glDeleteTexturesEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGenTexturesEXT = _get_function('glGenTexturesEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glIsTextureEXT = _get_function('glIsTextureEXT', [_ctypes.c_uint], _ctypes.c_ubyte)
glPrioritizeTexturesEXT = _get_function('glPrioritizeTexturesEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint), _ctypes.POINTER(_ctypes.c_float)], None)
