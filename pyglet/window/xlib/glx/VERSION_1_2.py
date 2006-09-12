
"""VERSION_1_2

"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
from pyglet.window.xlib.glx.VERSION_1_1 import *
glXGetCurrentDisplay = _get_function('glXGetCurrentDisplay', [], _ctypes.POINTER(Display))
