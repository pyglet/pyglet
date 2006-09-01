
"""ARB_window_pos
http://oss.sgi.com/projects/ogl-sample/registry/ARB/window_pos.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glWindowPos2dARB = _get_function('glWindowPos2dARB', [_ctypes.c_double, _ctypes.c_double], None)
glWindowPos2dvARB = _get_function('glWindowPos2dvARB', [_ctypes.POINTER(_ctypes.c_double)], None)
glWindowPos2fARB = _get_function('glWindowPos2fARB', [_ctypes.c_float, _ctypes.c_float], None)
glWindowPos2fvARB = _get_function('glWindowPos2fvARB', [_ctypes.POINTER(_ctypes.c_float)], None)
glWindowPos2iARB = _get_function('glWindowPos2iARB', [_ctypes.c_int, _ctypes.c_int], None)
glWindowPos2ivARB = _get_function('glWindowPos2ivARB', [_ctypes.POINTER(_ctypes.c_int)], None)
glWindowPos2sARB = _get_function('glWindowPos2sARB', [_ctypes.c_short, _ctypes.c_short], None)
glWindowPos2svARB = _get_function('glWindowPos2svARB', [_ctypes.POINTER(_ctypes.c_short)], None)
glWindowPos3dARB = _get_function('glWindowPos3dARB', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glWindowPos3dvARB = _get_function('glWindowPos3dvARB', [_ctypes.POINTER(_ctypes.c_double)], None)
glWindowPos3fARB = _get_function('glWindowPos3fARB', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glWindowPos3fvARB = _get_function('glWindowPos3fvARB', [_ctypes.POINTER(_ctypes.c_float)], None)
glWindowPos3iARB = _get_function('glWindowPos3iARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glWindowPos3ivARB = _get_function('glWindowPos3ivARB', [_ctypes.POINTER(_ctypes.c_int)], None)
glWindowPos3sARB = _get_function('glWindowPos3sARB', [_ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glWindowPos3svARB = _get_function('glWindowPos3svARB', [_ctypes.POINTER(_ctypes.c_short)], None)
