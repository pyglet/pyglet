
"""GREMEDY_string_marker
http://oss.sgi.com/projects/ogl-sample/registry/GREMEDY/string_marker.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glStringMarkerGREMEDY = _get_function('glStringMarkerGREMEDY', [_ctypes.c_int, _ctypes.c_void_p], None)
