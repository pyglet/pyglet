
"""SGIX_framezoom
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/framezoom.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glFrameZoomSGIX = _get_function('glFrameZoomSGIX', [_ctypes.c_int], None)
