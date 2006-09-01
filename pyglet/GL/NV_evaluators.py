
"""NV_evaluators
http://oss.sgi.com/projects/ogl-sample/registry/NV/evaluators.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_EVAL_2D_NV = 0x86C0
GL_EVAL_TRIANGULAR_2D_NV = 0x86C1
GL_MAP_TESSELLATION_NV = 0x86C2
GL_MAP_ATTRIB_U_ORDER_NV = 0x86C3
GL_MAP_ATTRIB_V_ORDER_NV = 0x86C4
GL_EVAL_FRACTIONAL_TESSELLATION_NV = 0x86C5
GL_EVAL_VERTEX_ATTRIB0_NV = 0x86C6
GL_EVAL_VERTEX_ATTRIB1_NV = 0x86C7
GL_EVAL_VERTEX_ATTRIB2_NV = 0x86C8
GL_EVAL_VERTEX_ATTRIB3_NV = 0x86C9
GL_EVAL_VERTEX_ATTRIB4_NV = 0x86CA
GL_EVAL_VERTEX_ATTRIB5_NV = 0x86CB
GL_EVAL_VERTEX_ATTRIB6_NV = 0x86CC
GL_EVAL_VERTEX_ATTRIB7_NV = 0x86CD
GL_EVAL_VERTEX_ATTRIB8_NV = 0x86CE
GL_EVAL_VERTEX_ATTRIB9_NV = 0x86CF
GL_EVAL_VERTEX_ATTRIB10_NV = 0x86D0
GL_EVAL_VERTEX_ATTRIB11_NV = 0x86D1
GL_EVAL_VERTEX_ATTRIB12_NV = 0x86D2
GL_EVAL_VERTEX_ATTRIB13_NV = 0x86D3
GL_EVAL_VERTEX_ATTRIB14_NV = 0x86D4
GL_EVAL_VERTEX_ATTRIB15_NV = 0x86D5
GL_MAX_MAP_TESSELLATION_NV = 0x86D6
GL_MAX_RATIONAL_EVAL_ORDER_NV = 0x86D7
glEvalMapsNV = _get_function('glEvalMapsNV', [_ctypes.c_uint, _ctypes.c_uint], None)
glGetMapAttribParameterfvNV = _get_function('glGetMapAttribParameterfvNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetMapAttribParameterivNV = _get_function('glGetMapAttribParameterivNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetMapControlPointsNV = _get_function('glGetMapControlPointsNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_ubyte, _ctypes.c_void_p], None)
glGetMapParameterfvNV = _get_function('glGetMapParameterfvNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetMapParameterivNV = _get_function('glGetMapParameterivNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glMapControlPointsNV = _get_function('glMapControlPointsNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_ubyte, _ctypes.c_void_p], None)
glMapParameterfvNV = _get_function('glMapParameterfvNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glMapParameterivNV = _get_function('glMapParameterivNV', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
