
"""SUN_global_alpha
http://oss.sgi.com/projects/ogl-sample/registry/SUN/global_alpha.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_GLOBAL_ALPHA_SUN = 0x81D9
GL_GLOBAL_ALPHA_FACTOR_SUN = 0x81DA
glGlobalAlphaFactorbSUN = _get_function('glGlobalAlphaFactorbSUN', [_ctypes.c_byte], None)
glGlobalAlphaFactordSUN = _get_function('glGlobalAlphaFactordSUN', [_ctypes.c_double], None)
glGlobalAlphaFactorfSUN = _get_function('glGlobalAlphaFactorfSUN', [_ctypes.c_float], None)
glGlobalAlphaFactoriSUN = _get_function('glGlobalAlphaFactoriSUN', [_ctypes.c_int], None)
glGlobalAlphaFactorsSUN = _get_function('glGlobalAlphaFactorsSUN', [_ctypes.c_short], None)
glGlobalAlphaFactorubSUN = _get_function('glGlobalAlphaFactorubSUN', [_ctypes.c_ubyte], None)
glGlobalAlphaFactoruiSUN = _get_function('glGlobalAlphaFactoruiSUN', [_ctypes.c_uint], None)
glGlobalAlphaFactorusSUN = _get_function('glGlobalAlphaFactorusSUN', [_ctypes.c_ushort], None)
