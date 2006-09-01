
"""EXT_framebuffer_blit
http://oss.sgi.com/projects/ogl-sample/registry/EXT/framebuffer_blit.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_DRAW_FRAMEBUFFER_BINDING_EXT = 0x8CA6
GL_READ_FRAMEBUFFER_EXT = 0x8CA8
GL_DRAW_FRAMEBUFFER_EXT = 0x8CA9
GL_READ_FRAMEBUFFER_BINDING_EXT = 0x8CAA
glBlitFramebufferEXT = _get_function('glBlitFramebufferEXT', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint], None)
