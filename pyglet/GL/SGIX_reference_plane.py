
"""SGIX_reference_plane
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/reference_plane.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glReferencePlaneSGIX = _get_function('glReferencePlaneSGIX', [_ctypes.POINTER(_ctypes.c_double)], None)
