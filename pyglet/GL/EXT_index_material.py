
"""EXT_index_material
http://oss.sgi.com/projects/ogl-sample/registry/EXT/index_material.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glIndexMaterialEXT = _get_function('glIndexMaterialEXT', [_ctypes.c_uint, _ctypes.c_uint], None)
