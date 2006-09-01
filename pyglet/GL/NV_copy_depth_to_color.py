
"""NV_copy_depth_to_color
http://oss.sgi.com/projects/ogl-sample/registry/NV/copy_depth_to_color.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_DEPTH_STENCIL_TO_RGBA_NV = 0x886E
GL_DEPTH_STENCIL_TO_BGRA_NV = 0x886F
