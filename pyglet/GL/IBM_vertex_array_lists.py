
"""IBM_vertex_array_lists
http://oss.sgi.com/projects/ogl-sample/registry/IBM/vertex_array_lists.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_VERTEX_ARRAY_LIST_IBM = 103070
GL_NORMAL_ARRAY_LIST_IBM = 103071
GL_COLOR_ARRAY_LIST_IBM = 103072
GL_INDEX_ARRAY_LIST_IBM = 103073
GL_TEXTURE_COORD_ARRAY_LIST_IBM = 103074
GL_EDGE_FLAG_ARRAY_LIST_IBM = 103075
GL_FOG_COORDINATE_ARRAY_LIST_IBM = 103076
GL_SECONDARY_COLOR_ARRAY_LIST_IBM = 103077
GL_VERTEX_ARRAY_LIST_STRIDE_IBM = 103080
GL_NORMAL_ARRAY_LIST_STRIDE_IBM = 103081
GL_COLOR_ARRAY_LIST_STRIDE_IBM = 103082
GL_INDEX_ARRAY_LIST_STRIDE_IBM = 103083
GL_TEXTURE_COORD_ARRAY_LIST_STRIDE_IBM = 103084
GL_EDGE_FLAG_ARRAY_LIST_STRIDE_IBM = 103085
GL_FOG_COORDINATE_ARRAY_LIST_STRIDE_IBM = 103086
GL_SECONDARY_COLOR_ARRAY_LIST_STRIDE_IBM = 103087
glColorPointerListIBM = _get_function('glColorPointerListIBM', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
glEdgeFlagPointerListIBM = _get_function('glEdgeFlagPointerListIBM', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_char_p), _ctypes.c_int], None)
glFogCoordPointerListIBM = _get_function('glFogCoordPointerListIBM', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
glIndexPointerListIBM = _get_function('glIndexPointerListIBM', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
glNormalPointerListIBM = _get_function('glNormalPointerListIBM', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
glSecondaryColorPointerListIBM = _get_function('glSecondaryColorPointerListIBM', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
glTexCoordPointerListIBM = _get_function('glTexCoordPointerListIBM', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
glVertexPointerListIBM = _get_function('glVertexPointerListIBM', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], None)
