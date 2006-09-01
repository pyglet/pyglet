
"""SGIS_multisample
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/multisample.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MULTISAMPLE_SGIS = 0x809D
GL_SAMPLE_ALPHA_TO_MASK_SGIS = 0x809E
GL_SAMPLE_ALPHA_TO_ONE_SGIS = 0x809F
GL_SAMPLE_MASK_SGIS = 0x80A0
GL_1PASS_SGIS = 0x80A1
GL_2PASS_0_SGIS = 0x80A2
GL_2PASS_1_SGIS = 0x80A3
GL_4PASS_0_SGIS = 0x80A4
GL_4PASS_1_SGIS = 0x80A5
GL_4PASS_2_SGIS = 0x80A6
GL_4PASS_3_SGIS = 0x80A7
GL_SAMPLE_BUFFERS_SGIS = 0x80A8
GL_SAMPLES_SGIS = 0x80A9
GL_SAMPLE_MASK_VALUE_SGIS = 0x80AA
GL_SAMPLE_MASK_INVERT_SGIS = 0x80AB
GL_SAMPLE_PATTERN_SGIS = 0x80AC
GL_MULTISAMPLE_BIT_EXT = 0x20000000
glSampleMaskSGIS = _get_function('glSampleMaskSGIS', [_ctypes.c_float, _ctypes.c_ubyte], None)
glSamplePatternSGIS = _get_function('glSamplePatternSGIS', [_ctypes.c_uint], None)
