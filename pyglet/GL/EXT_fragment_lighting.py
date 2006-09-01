
"""EXT_fragment_lighting
http://oss.sgi.com/projects/ogl-sample/registry/EXT/fragment_lighting.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_FRAGMENT_LIGHTING_EXT = 0x8400
GL_FRAGMENT_COLOR_MATERIAL_EXT = 0x8401
GL_FRAGMENT_COLOR_MATERIAL_FACE_EXT = 0x8402
GL_FRAGMENT_COLOR_MATERIAL_PARAMETER_EXT = 0x8403
GL_MAX_FRAGMENT_LIGHTS_EXT = 0x8404
GL_MAX_ACTIVE_LIGHTS_EXT = 0x8405
GL_CURRENT_RASTER_NORMAL_EXT = 0x8406
GL_LIGHT_ENV_MODE_EXT = 0x8407
GL_FRAGMENT_LIGHT_MODEL_LOCAL_VIEWER_EXT = 0x8408
GL_FRAGMENT_LIGHT_MODEL_TWO_SIDE_EXT = 0x8409
GL_FRAGMENT_LIGHT_MODEL_AMBIENT_EXT = 0x840A
GL_FRAGMENT_LIGHT_MODEL_NORMAL_INTERPOLATION_EXT = 0x840B
GL_FRAGMENT_LIGHT0_EXT = 0x840C
GL_FRAGMENT_LIGHT7_EXT = 0x8413
glFragmentColorMaterialEXT = _get_function('glFragmentColorMaterialEXT', [_ctypes.c_uint, _ctypes.c_uint], None)
glFragmentLightModelfEXT = _get_function('glFragmentLightModelfEXT', [_ctypes.c_uint, _ctypes.c_float], None)
glFragmentLightModelfvEXT = _get_function('glFragmentLightModelfvEXT', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glFragmentLightModeliEXT = _get_function('glFragmentLightModeliEXT', [_ctypes.c_uint, _ctypes.c_int], None)
glFragmentLightModelivEXT = _get_function('glFragmentLightModelivEXT', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glFragmentLightfEXT = _get_function('glFragmentLightfEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_float], None)
glFragmentLightfvEXT = _get_function('glFragmentLightfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glFragmentLightiEXT = _get_function('glFragmentLightiEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glFragmentLightivEXT = _get_function('glFragmentLightivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glFragmentMaterialfEXT = _get_function('glFragmentMaterialfEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_float], None)
glFragmentMaterialfvEXT = _get_function('glFragmentMaterialfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glFragmentMaterialiEXT = _get_function('glFragmentMaterialiEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glFragmentMaterialivEXT = _get_function('glFragmentMaterialivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetFragmentLightfvEXT = _get_function('glGetFragmentLightfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetFragmentLightivEXT = _get_function('glGetFragmentLightivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetFragmentMaterialfvEXT = _get_function('glGetFragmentMaterialfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetFragmentMaterialivEXT = _get_function('glGetFragmentMaterialivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glLightEnviEXT = _get_function('glLightEnviEXT', [_ctypes.c_uint, _ctypes.c_int], None)
