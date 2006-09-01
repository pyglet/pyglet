
"""ATI_separate_stencil
http://www.ati.com/developer/sdk/RadeonSDK/Html/Info/ATI_separate_stencil.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_STENCIL_BACK_FUNC_ATI = 0x8800
GL_STENCIL_BACK_FAIL_ATI = 0x8801
GL_STENCIL_BACK_PASS_DEPTH_FAIL_ATI = 0x8802
GL_STENCIL_BACK_PASS_DEPTH_PASS_ATI = 0x8803
glStencilOpSeparateATI = _get_function('glStencilOpSeparateATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glStencilFuncSeparateATI = _get_function('glStencilFuncSeparateATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint], None)
