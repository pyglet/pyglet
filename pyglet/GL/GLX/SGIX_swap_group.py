
"""SGIX_swap_group
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/swap_group.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXJoinSwapGroupSGIX = _get_function('glXJoinSwapGroupSGIX', [_ctypes.POINTER(Display), GLXDrawable, GLXDrawable], None)
