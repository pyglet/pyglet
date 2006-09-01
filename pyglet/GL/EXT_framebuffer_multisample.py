
"""EXT_framebuffer_multisample
http://oss.sgi.com/projects/ogl-sample/registry/EXT/framebuffer_multisample.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_RENDERBUFFER_SAMPLES_EXT = 0x8CAB
glRenderbufferStorageMultisampleEXT = _get_function('glRenderbufferStorageMultisampleEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int], None)
