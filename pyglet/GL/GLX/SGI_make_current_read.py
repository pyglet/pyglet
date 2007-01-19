
"""SGI_make_current_read
http://oss.sgi.com/projects/ogl-sample/registry/SGI/make_current_read.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXGetCurrentReadDrawableSGI = _get_function('glXGetCurrentReadDrawableSGI', [], GLXDrawable)
glXMakeCurrentReadSGI = _get_function('glXMakeCurrentReadSGI', [_ctypes.POINTER(Display), GLXDrawable, GLXDrawable, GLXContext], _ctypes.c_int)
