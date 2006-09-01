
"""EXT_texture_compression_s3tc
http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture_compression_s3tc.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_COMPRESSED_RGB_S3TC_DXT1_EXT = 0x83F0
GL_COMPRESSED_RGBA_S3TC_DXT1_EXT = 0x83F1
GL_COMPRESSED_RGBA_S3TC_DXT3_EXT = 0x83F2
GL_COMPRESSED_RGBA_S3TC_DXT5_EXT = 0x83F3
