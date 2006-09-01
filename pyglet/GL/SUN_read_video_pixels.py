
"""SUN_read_video_pixels
http://wwws.sun.com/software/graphics/opengl/extensions/gl_sun_read_video_pixels.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glReadVideoPixelsSUN = _get_function('glReadVideoPixelsSUN', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
