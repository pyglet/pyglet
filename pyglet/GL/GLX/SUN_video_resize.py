
"""SUN_video_resize
http://wwws.sun.com/software/graphics/opengl/extensions/glx_sun_video_resize.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_VIDEO_RESIZE_COMPENSATION_SUN = 0x85CD
GLX_VIDEO_RESIZE_SUN = 0x8171
glXVideoResizeSUN = _get_function('glXVideoResizeSUN', [_ctypes.POINTER(Display), GLXDrawable, float], _ctypes.c_int)
glXGetVideoResizeSUN = _get_function('glXGetVideoResizeSUN', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.POINTER(float)], _ctypes.c_int)
