
"""MESA_set_3dfx_mode
http://oss.sgi.com/projects/ogl-sample/registry/MESA/set_3dfx_mode.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GLX_3DFX_WINDOW_MODE_MESA = 0x1
GLX_3DFX_FULLSCREEN_MODE_MESA = 0x2
glXSet3DfxModeMESA = _get_function('glXSet3DfxModeMESA', [_ctypes.c_int], _ctypes.c_ubyte)
