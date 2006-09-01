
"""SGIX_fragment_specular_lighting
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/fragment_specular_lighting.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glFragmentColorMaterialSGIX = _get_function('glFragmentColorMaterialSGIX', [_ctypes.c_uint, _ctypes.c_uint], None)
glFragmentLightModelfSGIX = _get_function('glFragmentLightModelfSGIX', [_ctypes.c_uint, _ctypes.c_float], None)
glFragmentLightModelfvSGIX = _get_function('glFragmentLightModelfvSGIX', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glFragmentLightModeliSGIX = _get_function('glFragmentLightModeliSGIX', [_ctypes.c_uint, _ctypes.c_int], None)
glFragmentLightModelivSGIX = _get_function('glFragmentLightModelivSGIX', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glFragmentLightfSGIX = _get_function('glFragmentLightfSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_float], None)
glFragmentLightfvSGIX = _get_function('glFragmentLightfvSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glFragmentLightiSGIX = _get_function('glFragmentLightiSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glFragmentLightivSGIX = _get_function('glFragmentLightivSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glFragmentMaterialfSGIX = _get_function('glFragmentMaterialfSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_float], None)
glFragmentMaterialfvSGIX = _get_function('glFragmentMaterialfvSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glFragmentMaterialiSGIX = _get_function('glFragmentMaterialiSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glFragmentMaterialivSGIX = _get_function('glFragmentMaterialivSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetFragmentLightfvSGIX = _get_function('glGetFragmentLightfvSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetFragmentLightivSGIX = _get_function('glGetFragmentLightivSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetFragmentMaterialfvSGIX = _get_function('glGetFragmentMaterialfvSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetFragmentMaterialivSGIX = _get_function('glGetFragmentMaterialivSGIX', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
