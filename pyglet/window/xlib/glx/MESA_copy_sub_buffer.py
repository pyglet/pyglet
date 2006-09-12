
"""MESA_copy_sub_buffer
http://oss.sgi.com/projects/ogl-sample/registry/MESA/copy_sub_buffer.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXCopySubBufferMESA = _get_function('glXCopySubBufferMESA', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
