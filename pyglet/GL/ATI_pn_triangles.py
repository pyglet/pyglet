
"""ATI_pn_triangles
http://www.ati.com/developer/sdk/RADEONSDK/Html/Info/ati_pn_triangles.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PN_TRIANGLES_ATI = 0x87F0
GL_MAX_PN_TRIANGLES_TESSELATION_LEVEL_ATI = 0x87F1
GL_PN_TRIANGLES_POINT_MODE_ATI = 0x87F2
GL_PN_TRIANGLES_NORMAL_MODE_ATI = 0x87F3
GL_PN_TRIANGLES_TESSELATION_LEVEL_ATI = 0x87F4
GL_PN_TRIANGLES_POINT_MODE_LINEAR_ATI = 0x87F5
GL_PN_TRIANGLES_POINT_MODE_CUBIC_ATI = 0x87F6
GL_PN_TRIANGLES_NORMAL_MODE_LINEAR_ATI = 0x87F7
GL_PN_TRIANGLES_NORMAL_MODE_QUADRATIC_ATI = 0x87F8
glPNTrianglesiATI = _get_function('glPNTrianglesiATI', [_ctypes.c_uint, _ctypes.c_int], None)
glPNTrianglesfATI = _get_function('glPNTrianglesfATI', [_ctypes.c_uint, _ctypes.c_float], None)
