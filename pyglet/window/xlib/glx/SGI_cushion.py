
"""SGI_cushion
http://oss.sgi.com/projects/ogl-sample/registry/SGI/cushion.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXCushionSGI = _get_function('glXCushionSGI', [_ctypes.POINTER(Display), _ctypes.c_ulong, float], None)
