
"""ATI_fragment_shader
http://oss.sgi.com/projects/ogl-sample/registry/ATI/fragment_shader.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_RED_BIT_ATI = 0x00000001
GL_2X_BIT_ATI = 0x00000001
GL_4X_BIT_ATI = 0x00000002
GL_GREEN_BIT_ATI = 0x00000002
GL_COMP_BIT_ATI = 0x00000002
GL_BLUE_BIT_ATI = 0x00000004
GL_8X_BIT_ATI = 0x00000004
GL_NEGATE_BIT_ATI = 0x00000004
GL_BIAS_BIT_ATI = 0x00000008
GL_HALF_BIT_ATI = 0x00000008
GL_QUARTER_BIT_ATI = 0x00000010
GL_EIGHTH_BIT_ATI = 0x00000020
GL_SATURATE_BIT_ATI = 0x00000040
GL_FRAGMENT_SHADER_ATI = 0x8920
GL_REG_0_ATI = 0x8921
GL_REG_1_ATI = 0x8922
GL_REG_2_ATI = 0x8923
GL_REG_3_ATI = 0x8924
GL_REG_4_ATI = 0x8925
GL_REG_5_ATI = 0x8926
GL_CON_0_ATI = 0x8941
GL_CON_1_ATI = 0x8942
GL_CON_2_ATI = 0x8943
GL_CON_3_ATI = 0x8944
GL_CON_4_ATI = 0x8945
GL_CON_5_ATI = 0x8946
GL_CON_6_ATI = 0x8947
GL_CON_7_ATI = 0x8948
GL_MOV_ATI = 0x8961
GL_ADD_ATI = 0x8963
GL_MUL_ATI = 0x8964
GL_SUB_ATI = 0x8965
GL_DOT3_ATI = 0x8966
GL_DOT4_ATI = 0x8967
GL_MAD_ATI = 0x8968
GL_LERP_ATI = 0x8969
GL_CND_ATI = 0x896A
GL_CND0_ATI = 0x896B
GL_DOT2_ADD_ATI = 0x896C
GL_SECONDARY_INTERPOLATOR_ATI = 0x896D
GL_SWIZZLE_STR_ATI = 0x8976
GL_SWIZZLE_STQ_ATI = 0x8977
GL_SWIZZLE_STR_DR_ATI = 0x8978
GL_SWIZZLE_STQ_DQ_ATI = 0x8979
GL_NUM_FRAGMENT_REGISTERS_ATI = 0x896E
GL_NUM_FRAGMENT_CONSTANTS_ATI = 0x896F
GL_NUM_PASSES_ATI = 0x8970
GL_NUM_INSTRUCTIONS_PER_PASS_ATI = 0x8971
GL_NUM_INSTRUCTIONS_TOTAL_ATI = 0x8972
GL_NUM_INPUT_INTERPOLATOR_COMPONENTS_ATI = 0x8973
GL_NUM_LOOPBACK_COMPONENTS_ATI = 0x8974
GL_COLOR_ALPHA_PAIRING_ATI = 0x8975
GL_SWIZZLE_STRQ_ATI = 0x897A
GL_SWIZZLE_STRQ_DQ_ATI = 0x897B
glAlphaFragmentOp1ATI = _get_function('glAlphaFragmentOp1ATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glAlphaFragmentOp2ATI = _get_function('glAlphaFragmentOp2ATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glAlphaFragmentOp3ATI = _get_function('glAlphaFragmentOp3ATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glBeginFragmentShaderATI = _get_function('glBeginFragmentShaderATI', [], None)
glBindFragmentShaderATI = _get_function('glBindFragmentShaderATI', [_ctypes.c_uint], None)
glColorFragmentOp1ATI = _get_function('glColorFragmentOp1ATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glColorFragmentOp2ATI = _get_function('glColorFragmentOp2ATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glColorFragmentOp3ATI = _get_function('glColorFragmentOp3ATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glDeleteFragmentShaderATI = _get_function('glDeleteFragmentShaderATI', [_ctypes.c_uint], None)
glEndFragmentShaderATI = _get_function('glEndFragmentShaderATI', [], None)
glGenFragmentShadersATI = _get_function('glGenFragmentShadersATI', [_ctypes.c_uint], _ctypes.c_uint)
glPassTexCoordATI = _get_function('glPassTexCoordATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glSampleMapATI = _get_function('glSampleMapATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glSetFragmentShaderConstantATI = _get_function('glSetFragmentShaderConstantATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
