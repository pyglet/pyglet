
"""SGI_swap_control
http://oss.sgi.com/projects/ogl-sample/registry/SGI/swap_control.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXSwapIntervalSGI = _get_function('glXSwapIntervalSGI', [_ctypes.c_int], _ctypes.c_int)
