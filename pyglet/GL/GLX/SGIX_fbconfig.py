
"""SGIX_fbconfig
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/fbconfig.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GLX_WINDOW_BIT_SGIX = 0x00000001
GLX_RGBA_BIT_SGIX = 0x00000001
GLX_PIXMAP_BIT_SGIX = 0x00000002
GLX_COLOR_INDEX_BIT_SGIX = 0x00000002
GLX_SCREEN_EXT = 0x800C
GLX_DRAWABLE_TYPE_SGIX = 0x8010
GLX_RENDER_TYPE_SGIX = 0x8011
GLX_X_RENDERABLE_SGIX = 0x8012
GLX_FBCONFIG_ID_SGIX = 0x8013
GLX_RGBA_TYPE_SGIX = 0x8014
GLX_COLOR_INDEX_TYPE_SGIX = 0x8015
GLXFBConfigIDSGIX = _ctypes.c_ulong
glXChooseFBConfigSGIX = _get_function('glXChooseFBConfigSGIX', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], _ctypes.POINTER(GLXFBConfigSGIX))
glXCreateContextWithConfigSGIX = _get_function('glXCreateContextWithConfigSGIX', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.c_int, GLXContext, _ctypes.c_int], GLXContext)
glXCreateGLXPixmapWithConfigSGIX = _get_function('glXCreateGLXPixmapWithConfigSGIX', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.c_ulong], GLXPixmap)
glXGetFBConfigAttribSGIX = _get_function('glXGetFBConfigAttribSGIX', [_ctypes.POINTER(Display), GLXFBConfigSGIX, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
glXGetFBConfigFromVisualSGIX = _get_function('glXGetFBConfigFromVisualSGIX', [_ctypes.POINTER(Display), _ctypes.POINTER(XVisualInfo)], GLXFBConfigSGIX)
glXGetVisualFromFBConfigSGIX = _get_function('glXGetVisualFromFBConfigSGIX', [_ctypes.POINTER(Display), GLXFBConfig], _ctypes.POINTER(XVisualInfo))
