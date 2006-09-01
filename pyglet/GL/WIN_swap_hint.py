
"""WIN_swap_hint
http://msdn.microsoft.com/library/default.asp?url=/library/en-us/opengl/glfunc01_16zy.asp
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glAddSwapHintRectWIN = _get_function('glAddSwapHintRectWIN', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
