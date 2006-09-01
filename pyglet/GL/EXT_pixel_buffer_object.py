
"""EXT_pixel_buffer_object
http://www.nvidia.com/dev_content/nvopenglspecs/GL_EXT_pixel_buffer_object.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PIXEL_PACK_BUFFER_EXT = 0x88EB
GL_PIXEL_UNPACK_BUFFER_EXT = 0x88EC
GL_PIXEL_PACK_BUFFER_BINDING_EXT = 0x88ED
GL_PIXEL_UNPACK_BUFFER_BINDING_EXT = 0x88EF
