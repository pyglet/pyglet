
"""ARB_texture_compression
http://oss.sgi.com/projects/ogl-sample/registry/ARB/texture_compression.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_COMPRESSED_ALPHA_ARB = 0x84E9
GL_COMPRESSED_LUMINANCE_ARB = 0x84EA
GL_COMPRESSED_LUMINANCE_ALPHA_ARB = 0x84EB
GL_COMPRESSED_INTENSITY_ARB = 0x84EC
GL_COMPRESSED_RGB_ARB = 0x84ED
GL_COMPRESSED_RGBA_ARB = 0x84EE
GL_TEXTURE_COMPRESSION_HINT_ARB = 0x84EF
GL_TEXTURE_COMPRESSED_IMAGE_SIZE_ARB = 0x86A0
GL_TEXTURE_COMPRESSED_ARB = 0x86A1
GL_NUM_COMPRESSED_TEXTURE_FORMATS_ARB = 0x86A2
GL_COMPRESSED_TEXTURE_FORMATS_ARB = 0x86A3
glCompressedTexImage1DARB = _get_function('glCompressedTexImage1DARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], None)
glCompressedTexImage2DARB = _get_function('glCompressedTexImage2DARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], None)
glCompressedTexImage3DARB = _get_function('glCompressedTexImage3DARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], None)
glCompressedTexSubImage1DARB = _get_function('glCompressedTexSubImage1DARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glCompressedTexSubImage2DARB = _get_function('glCompressedTexSubImage2DARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glCompressedTexSubImage3DARB = _get_function('glCompressedTexSubImage3DARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glGetCompressedTexImageARB = _get_function('glGetCompressedTexImageARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
