
"""EXT_depth_bounds_test
http://www.nvidia.com/dev_content/nvopenglspecs/GL_EXT_depth_bounds_test.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_DEPTH_BOUNDS_TEST_EXT = 0x8890
GL_DEPTH_BOUNDS_EXT = 0x8891
glDepthBoundsEXT = _get_function('glDepthBoundsEXT', [_ctypes.c_double, _ctypes.c_double], None)
