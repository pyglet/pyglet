
"""ARB_multisample
http://oss.sgi.com/projects/ogl-sample/registry/ARB/multisample.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MULTISAMPLE_ARB = 0x809D
GL_SAMPLE_ALPHA_TO_COVERAGE_ARB = 0x809E
GL_SAMPLE_ALPHA_TO_ONE_ARB = 0x809F
GL_SAMPLE_COVERAGE_ARB = 0x80A0
GL_SAMPLE_BUFFERS_ARB = 0x80A8
GL_SAMPLES_ARB = 0x80A9
GL_SAMPLE_COVERAGE_VALUE_ARB = 0x80AA
GL_SAMPLE_COVERAGE_INVERT_ARB = 0x80AB
GL_MULTISAMPLE_BIT_ARB = 0x20000000
glSampleCoverageARB = _get_function('glSampleCoverageARB', [_ctypes.c_float, _ctypes.c_ubyte], None)
