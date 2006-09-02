
"""ARB_vertex_blend
http://oss.sgi.com/projects/ogl-sample/registry/ARB/vertex_blend.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MAX_VERTEX_UNITS_ARB = 0x86A4
GL_ACTIVE_VERTEX_UNITS_ARB = 0x86A5
GL_WEIGHT_SUM_UNITY_ARB = 0x86A6
GL_VERTEX_BLEND_ARB = 0x86A7
GL_CURRENT_WEIGHT_ARB = 0x86A8
GL_WEIGHT_ARRAY_TYPE_ARB = 0x86A9
GL_WEIGHT_ARRAY_STRIDE_ARB = 0x86AA
GL_WEIGHT_ARRAY_SIZE_ARB = 0x86AB
GL_WEIGHT_ARRAY_POINTER_ARB = 0x86AC
GL_WEIGHT_ARRAY_ARB = 0x86AD
GL_MODELVIEW0_ARB = 0x1700
GL_MODELVIEW1_ARB = 0x850A
GL_MODELVIEW2_ARB = 0x8722
GL_MODELVIEW3_ARB = 0x8723
GL_MODELVIEW4_ARB = 0x8724
GL_MODELVIEW5_ARB = 0x8725
GL_MODELVIEW6_ARB = 0x8726
GL_MODELVIEW7_ARB = 0x8727
GL_MODELVIEW8_ARB = 0x8728
GL_MODELVIEW9_ARB = 0x8729
GL_MODELVIEW10_ARB = 0x872A
GL_MODELVIEW11_ARB = 0x872B
GL_MODELVIEW12_ARB = 0x872C
GL_MODELVIEW13_ARB = 0x872D
GL_MODELVIEW14_ARB = 0x872E
GL_MODELVIEW15_ARB = 0x872F
GL_MODELVIEW16_ARB = 0x8730
GL_MODELVIEW17_ARB = 0x8731
GL_MODELVIEW18_ARB = 0x8732
GL_MODELVIEW19_ARB = 0x8733
GL_MODELVIEW20_ARB = 0x8734
GL_MODELVIEW21_ARB = 0x8735
GL_MODELVIEW22_ARB = 0x8736
GL_MODELVIEW23_ARB = 0x8737
GL_MODELVIEW24_ARB = 0x8738
GL_MODELVIEW25_ARB = 0x8739
GL_MODELVIEW26_ARB = 0x873A
GL_MODELVIEW27_ARB = 0x873B
GL_MODELVIEW28_ARB = 0x873C
GL_MODELVIEW29_ARB = 0x873D
GL_MODELVIEW30_ARB = 0x873E
GL_MODELVIEW31_ARB = 0x873F
glWeightbvARB = _get_function('glWeightbvARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_byte)], None)
glWeightsvARB = _get_function('glWeightsvARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_short)], None)
glWeightivARB = _get_function('glWeightivARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], None)
glWeightfvARB = _get_function('glWeightfvARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glWeightdvARB = _get_function('glWeightdvARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_double)], None)
glWeightubvARB = _get_function('glWeightubvARB', [_ctypes.c_int, _ctypes.c_char_p], None)
glWeightusvARB = _get_function('glWeightusvARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_ushort)], None)
glWeightuivARB = _get_function('glWeightuivARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glWeightPointerARB = _get_function('glWeightPointerARB', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glVertexBlendARB = _get_function('glVertexBlendARB', [_ctypes.c_int], None)
