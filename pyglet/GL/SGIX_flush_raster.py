
"""SGIX_flush_raster
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/flush_raster.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glFlushRasterSGIX = _get_function('glFlushRasterSGIX', [], None)
