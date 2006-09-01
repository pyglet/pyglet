
"""EXT_polygon_offset
http://oss.sgi.com/projects/ogl-sample/registry/EXT/polygon_offset.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_POLYGON_OFFSET_EXT = 0x8037
GL_POLYGON_OFFSET_FACTOR_EXT = 0x8038
GL_POLYGON_OFFSET_BIAS_EXT = 0x8039
glPolygonOffsetEXT = _get_function('glPolygonOffsetEXT', [_ctypes.c_float, _ctypes.c_float], None)
