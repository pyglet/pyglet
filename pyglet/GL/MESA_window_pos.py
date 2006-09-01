
"""MESA_window_pos
http://oss.sgi.com/projects/ogl-sample/registry/MESA/window_pos.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glWindowPos2dMESA = _get_function('glWindowPos2dMESA', [_ctypes.c_double, _ctypes.c_double], None)
glWindowPos2dvMESA = _get_function('glWindowPos2dvMESA', [_ctypes.POINTER(_ctypes.c_double)], None)
glWindowPos2fMESA = _get_function('glWindowPos2fMESA', [_ctypes.c_float, _ctypes.c_float], None)
glWindowPos2fvMESA = _get_function('glWindowPos2fvMESA', [_ctypes.POINTER(_ctypes.c_float)], None)
glWindowPos2iMESA = _get_function('glWindowPos2iMESA', [_ctypes.c_int, _ctypes.c_int], None)
glWindowPos2ivMESA = _get_function('glWindowPos2ivMESA', [_ctypes.POINTER(_ctypes.c_int)], None)
glWindowPos2sMESA = _get_function('glWindowPos2sMESA', [_ctypes.c_short, _ctypes.c_short], None)
glWindowPos2svMESA = _get_function('glWindowPos2svMESA', [_ctypes.POINTER(_ctypes.c_short)], None)
glWindowPos3dMESA = _get_function('glWindowPos3dMESA', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glWindowPos3dvMESA = _get_function('glWindowPos3dvMESA', [_ctypes.POINTER(_ctypes.c_double)], None)
glWindowPos3fMESA = _get_function('glWindowPos3fMESA', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glWindowPos3fvMESA = _get_function('glWindowPos3fvMESA', [_ctypes.POINTER(_ctypes.c_float)], None)
glWindowPos3iMESA = _get_function('glWindowPos3iMESA', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glWindowPos3ivMESA = _get_function('glWindowPos3ivMESA', [_ctypes.POINTER(_ctypes.c_int)], None)
glWindowPos3sMESA = _get_function('glWindowPos3sMESA', [_ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glWindowPos3svMESA = _get_function('glWindowPos3svMESA', [_ctypes.POINTER(_ctypes.c_short)], None)
glWindowPos4dMESA = _get_function('glWindowPos4dMESA', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glWindowPos4dvMESA = _get_function('glWindowPos4dvMESA', [_ctypes.POINTER(_ctypes.c_double)], None)
glWindowPos4fMESA = _get_function('glWindowPos4fMESA', [_ctypes.c_float, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glWindowPos4fvMESA = _get_function('glWindowPos4fvMESA', [_ctypes.POINTER(_ctypes.c_float)], None)
glWindowPos4iMESA = _get_function('glWindowPos4iMESA', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glWindowPos4ivMESA = _get_function('glWindowPos4ivMESA', [_ctypes.POINTER(_ctypes.c_int)], None)
glWindowPos4sMESA = _get_function('glWindowPos4sMESA', [_ctypes.c_short, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glWindowPos4svMESA = _get_function('glWindowPos4svMESA', [_ctypes.POINTER(_ctypes.c_short)], None)
