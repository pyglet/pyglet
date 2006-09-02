
"""SUN_triangle_list
http://oss.sgi.com/projects/ogl-sample/registry/SUN/triangle_list.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_RESTART_SUN = 0x01
GL_REPLACE_MIDDLE_SUN = 0x02
GL_REPLACE_OLDEST_SUN = 0x03
GL_TRIANGLE_LIST_SUN = 0x81D7
GL_REPLACEMENT_CODE_SUN = 0x81D8
GL_REPLACEMENT_CODE_ARRAY_SUN = 0x85C0
GL_REPLACEMENT_CODE_ARRAY_TYPE_SUN = 0x85C1
GL_REPLACEMENT_CODE_ARRAY_STRIDE_SUN = 0x85C2
GL_REPLACEMENT_CODE_ARRAY_POINTER_SUN = 0x85C3
GL_R1UI_V3F_SUN = 0x85C4
GL_R1UI_C4UB_V3F_SUN = 0x85C5
GL_R1UI_C3F_V3F_SUN = 0x85C6
GL_R1UI_N3F_V3F_SUN = 0x85C7
GL_R1UI_C4F_N3F_V3F_SUN = 0x85C8
GL_R1UI_T2F_V3F_SUN = 0x85C9
GL_R1UI_T2F_N3F_V3F_SUN = 0x85CA
GL_R1UI_T2F_C4F_N3F_V3F_SUN = 0x85CB
glReplacementCodePointerSUN = _get_function('glReplacementCodePointerSUN', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glReplacementCodeubSUN = _get_function('glReplacementCodeubSUN', [_ctypes.c_ubyte], None)
glReplacementCodeubvSUN = _get_function('glReplacementCodeubvSUN', [_ctypes.c_char_p], None)
glReplacementCodeuiSUN = _get_function('glReplacementCodeuiSUN', [_ctypes.c_uint], None)
glReplacementCodeuivSUN = _get_function('glReplacementCodeuivSUN', [_ctypes.POINTER(_ctypes.c_uint)], None)
glReplacementCodeusSUN = _get_function('glReplacementCodeusSUN', [_ctypes.c_ushort], None)
glReplacementCodeusvSUN = _get_function('glReplacementCodeusvSUN', [_ctypes.POINTER(_ctypes.c_ushort)], None)
