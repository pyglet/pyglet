
"""EXT_light_texture
http://oss.sgi.com/projects/ogl-sample/registry/EXT/light_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_FRAGMENT_MATERIAL_EXT = 0x8349
GL_FRAGMENT_NORMAL_EXT = 0x834A
GL_FRAGMENT_COLOR_EXT = 0x834C
GL_ATTENUATION_EXT = 0x834D
GL_SHADOW_ATTENUATION_EXT = 0x834E
GL_TEXTURE_APPLICATION_MODE_EXT = 0x834F
GL_TEXTURE_LIGHT_EXT = 0x8350
GL_TEXTURE_MATERIAL_FACE_EXT = 0x8351
GL_TEXTURE_MATERIAL_PARAMETER_EXT = 0x8352
GL_FRAGMENT_DEPTH_EXT = 0x8452
glApplyTextureEXT = _get_function('glApplyTextureEXT', [_ctypes.c_uint], None)
glTextureLightEXT = _get_function('glTextureLightEXT', [_ctypes.c_uint], None)
glTextureMaterialEXT = _get_function('glTextureMaterialEXT', [_ctypes.c_uint, _ctypes.c_uint], None)
