
"""MESA_resize_buffers
http://oss.sgi.com/projects/ogl-sample/registry/MESA/resize_buffers.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glResizeBuffersMESA = _get_function('glResizeBuffersMESA', [], None)
