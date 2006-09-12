
"""SGIX_swap_barrier
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/swap_barrier.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXBindSwapBarrierSGIX = _get_function('glXBindSwapBarrierSGIX', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.c_int], None)
glXQueryMaxSwapBarriersSGIX = _get_function('glXQueryMaxSwapBarriersSGIX', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
