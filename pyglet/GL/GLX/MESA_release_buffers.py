
"""MESA_release_buffers
http://oss.sgi.com/projects/ogl-sample/registry/MESA/release_buffers.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXReleaseBuffersMESA = _get_function('glXReleaseBuffersMESA', [_ctypes.POINTER(Display), GLXDrawable], _ctypes.c_int)
