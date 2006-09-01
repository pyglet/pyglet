
"""EXT_texture3D
http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture3D.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PACK_SKIP_IMAGES_EXT = 0x806B
GL_PACK_IMAGE_HEIGHT_EXT = 0x806C
GL_UNPACK_SKIP_IMAGES_EXT = 0x806D
GL_UNPACK_IMAGE_HEIGHT_EXT = 0x806E
GL_TEXTURE_3D_EXT = 0x806F
GL_PROXY_TEXTURE_3D_EXT = 0x8070
GL_TEXTURE_DEPTH_EXT = 0x8071
GL_TEXTURE_WRAP_R_EXT = 0x8072
GL_MAX_3D_TEXTURE_SIZE_EXT = 0x8073
glTexImage3DEXT = _get_function('glTexImage3DEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
