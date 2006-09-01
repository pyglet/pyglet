
"""KTX_buffer_region
GL_KTX_FRONT_REGION 0x0
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_KTX_BACK_REGION = 0x1
GL_KTX_Z_REGION = 0x2
GL_KTX_STENCIL_REGION = 0x3
glBufferRegionEnabledEXT = _get_function('glBufferRegionEnabledEXT', [], _ctypes.c_uint)
glNewBufferRegionEXT = _get_function('glNewBufferRegionEXT', [_ctypes.c_uint], _ctypes.c_uint)
glDeleteBufferRegionEXT = _get_function('glDeleteBufferRegionEXT', [_ctypes.c_uint], None)
glReadBufferRegionEXT = _get_function('glReadBufferRegionEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glDrawBufferRegionEXT = _get_function('glDrawBufferRegionEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
