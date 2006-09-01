
"""NV_fragment_program2
http://www.nvidia.com/dev_content/nvopenglspecs/GL_NV_fragment_program2.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MAX_PROGRAM_EXEC_INSTRUCTIONS_NV = 0x88F4
GL_MAX_PROGRAM_CALL_DEPTH_NV = 0x88F5
GL_MAX_PROGRAM_IF_DEPTH_NV = 0x88F6
GL_MAX_PROGRAM_LOOP_DEPTH_NV = 0x88F7
GL_MAX_PROGRAM_LOOP_COUNT_NV = 0x88F8
