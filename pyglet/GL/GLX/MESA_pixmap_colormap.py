
"""MESA_pixmap_colormap
http://oss.sgi.com/projects/ogl-sample/registry/MESA/pixmap_colormap.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXCreateGLXPixmapMESA = _get_function('glXCreateGLXPixmapMESA', [_ctypes.POINTER(Display), _ctypes.POINTER(XVisualInfo), _ctypes.c_ulong, Colormap], GLXPixmap)
