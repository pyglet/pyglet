
"""ATIX_texture_env_combine3
http://www.ati.com/developer/atiopengl.pdf
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MODULATE_ADD_ATIX = 0x8744
GL_MODULATE_SIGNED_ADD_ATIX = 0x8745
GL_MODULATE_SUBTRACT_ATIX = 0x8746
