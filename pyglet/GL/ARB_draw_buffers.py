
"""ARB_draw_buffers
http://oss.sgi.com/projects/ogl-sample/registry/ARB/draw_buffers.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MAX_DRAW_BUFFERS_ARB = 0x8824
GL_DRAW_BUFFER0_ARB = 0x8825
GL_DRAW_BUFFER1_ARB = 0x8826
GL_DRAW_BUFFER2_ARB = 0x8827
GL_DRAW_BUFFER3_ARB = 0x8828
GL_DRAW_BUFFER4_ARB = 0x8829
GL_DRAW_BUFFER5_ARB = 0x882A
GL_DRAW_BUFFER6_ARB = 0x882B
GL_DRAW_BUFFER7_ARB = 0x882C
GL_DRAW_BUFFER8_ARB = 0x882D
GL_DRAW_BUFFER9_ARB = 0x882E
GL_DRAW_BUFFER10_ARB = 0x882F
GL_DRAW_BUFFER11_ARB = 0x8830
GL_DRAW_BUFFER12_ARB = 0x8831
GL_DRAW_BUFFER13_ARB = 0x8832
GL_DRAW_BUFFER14_ARB = 0x8833
GL_DRAW_BUFFER15_ARB = 0x8834
glDrawBuffersARB = _get_function('glDrawBuffersARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
