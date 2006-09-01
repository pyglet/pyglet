
"""3DFX_tbuffer
http://oss.sgi.com/projects/ogl-sample/registry/3DFX/tbuffer.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glTbufferMask3DFX = _get_function('glTbufferMask3DFX', [_ctypes.c_uint], None)
