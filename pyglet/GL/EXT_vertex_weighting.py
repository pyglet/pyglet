
"""EXT_vertex_weighting
http://oss.sgi.com/projects/ogl-sample/registry/EXT/vertex_weighting.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MODELVIEW0_STACK_DEPTH_EXT = 0x0BA3
GL_MODELVIEW0_MATRIX_EXT = 0x0BA6
GL_MODELVIEW0_EXT = 0x1700
GL_MODELVIEW1_STACK_DEPTH_EXT = 0x8502
GL_MODELVIEW1_MATRIX_EXT = 0x8506
GL_VERTEX_WEIGHTING_EXT = 0x8509
GL_MODELVIEW1_EXT = 0x850A
GL_CURRENT_VERTEX_WEIGHT_EXT = 0x850B
GL_VERTEX_WEIGHT_ARRAY_EXT = 0x850C
GL_VERTEX_WEIGHT_ARRAY_SIZE_EXT = 0x850D
GL_VERTEX_WEIGHT_ARRAY_TYPE_EXT = 0x850E
GL_VERTEX_WEIGHT_ARRAY_STRIDE_EXT = 0x850F
GL_VERTEX_WEIGHT_ARRAY_POINTER_EXT = 0x8510
glVertexWeightPointerEXT = _get_function('glVertexWeightPointerEXT', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glVertexWeightfEXT = _get_function('glVertexWeightfEXT', [_ctypes.c_float], None)
glVertexWeightfvEXT = _get_function('glVertexWeightfvEXT', [_ctypes.POINTER(_ctypes.c_float)], None)
