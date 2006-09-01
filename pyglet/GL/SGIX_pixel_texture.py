
"""SGIX_pixel_texture
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/sgix_pixel_texture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glPixelTexGenSGIX = _get_function('glPixelTexGenSGIX', [_ctypes.c_uint], None)
