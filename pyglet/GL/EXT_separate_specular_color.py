
"""EXT_separate_specular_color
http://oss.sgi.com/projects/ogl-sample/registry/EXT/separate_specular_color.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_LIGHT_MODEL_COLOR_CONTROL_EXT = 0x81F8
GL_SINGLE_COLOR_EXT = 0x81F9
GL_SEPARATE_SPECULAR_COLOR_EXT = 0x81FA
