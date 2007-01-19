
"""VERSION_1_3

"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
from pyglet.GL.GLX.VERSION_1_2 import *
GLX_WINDOW_BIT = 0x00000001
GLX_PIXMAP_BIT = 0x00000002
GLX_PBUFFER_BIT = 0x00000004
GLX_RGBA_BIT = 0x00000001
GLX_COLOR_INDEX_BIT = 0x00000002
GLX_PBUFFER_CLOBBER_MASK = 0x08000000
GLX_FRONT_LEFT_BUFFER_BIT = 0x00000001
GLX_FRONT_RIGHT_BUFFER_BIT = 0x00000002
GLX_BACK_LEFT_BUFFER_BIT = 0x00000004
GLX_BACK_RIGHT_BUFFER_BIT = 0x00000008
GLX_AUX_BUFFERS_BIT = 0x00000010
GLX_DEPTH_BUFFER_BIT = 0x00000020
GLX_STENCIL_BUFFER_BIT = 0x00000040
GLX_ACCUM_BUFFER_BIT = 0x00000080
GLX_CONFIG_CAVEAT = 0x20
GLX_X_VISUAL_TYPE = 0x22
GLX_TRANSPARENT_TYPE = 0x23
GLX_TRANSPARENT_INDEX_VALUE = 0x24
GLX_TRANSPARENT_RED_VALUE = 0x25
GLX_TRANSPARENT_GREEN_VALUE = 0x26
GLX_TRANSPARENT_BLUE_VALUE = 0x27
GLX_TRANSPARENT_ALPHA_VALUE = 0x28
GLX_DONT_CARE = 0xFFFFFFFF
GLX_NONE = 0x8000
GLX_SLOW_CONFIG = 0x8001
GLX_TRUE_COLOR = 0x8002
GLX_DIRECT_COLOR = 0x8003
GLX_PSEUDO_COLOR = 0x8004
GLX_STATIC_COLOR = 0x8005
GLX_GRAY_SCALE = 0x8006
GLX_STATIC_GRAY = 0x8007
GLX_TRANSPARENT_RGB = 0x8008
GLX_TRANSPARENT_INDEX = 0x8009
GLX_VISUAL_ID = 0x800B
GLX_SCREEN = 0x800C
GLX_NON_CONFORMANT_CONFIG = 0x800D
GLX_DRAWABLE_TYPE = 0x8010
GLX_RENDER_TYPE = 0x8011
GLX_X_RENDERABLE = 0x8012
GLX_FBCONFIG_ID = 0x8013
GLX_RGBA_TYPE = 0x8014
GLX_COLOR_INDEX_TYPE = 0x8015
GLX_MAX_PBUFFER_WIDTH = 0x8016
GLX_MAX_PBUFFER_HEIGHT = 0x8017
GLX_MAX_PBUFFER_PIXELS = 0x8018
GLX_PRESERVED_CONTENTS = 0x801B
GLX_LARGEST_PBUFFER = 0x801C
GLX_WIDTH = 0x801D
GLX_HEIGHT = 0x801E
GLX_EVENT_MASK = 0x801F
GLX_DAMAGED = 0x8020
GLX_SAVED = 0x8021
GLX_WINDOW = 0x8022
GLX_PBUFFER = 0x8023
GLX_PBUFFER_HEIGHT = 0x8040
GLX_PBUFFER_WIDTH = 0x8041
GLXWindow = _ctypes.c_ulong
GLXPbuffer = _ctypes.c_ulong
GLXFBConfigID = _ctypes.c_ulong
glXChooseFBConfig = _get_function('glXChooseFBConfig', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], _ctypes.POINTER(GLXFBConfig))
glXGetFBConfigs = _get_function('glXGetFBConfigs', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.POINTER(GLXFBConfig))
glXGetVisualFromFBConfig = _get_function('glXGetVisualFromFBConfig', [_ctypes.POINTER(Display), GLXFBConfig], _ctypes.POINTER(XVisualInfo))
glXGetFBConfigAttrib = _get_function('glXGetFBConfigAttrib', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
glXCreateWindow = _get_function('glXCreateWindow', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.c_ulong, _ctypes.POINTER(_ctypes.c_int)], GLXWindow)
glXDestroyWindow = _get_function('glXDestroyWindow', [_ctypes.POINTER(Display), GLXWindow], None)
glXCreatePixmap = _get_function('glXCreatePixmap', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.c_ulong, _ctypes.POINTER(_ctypes.c_int)], GLXPixmap)
glXDestroyPixmap = _get_function('glXDestroyPixmap', [_ctypes.POINTER(Display), GLXPixmap], None)
glXCreatePbuffer = _get_function('glXCreatePbuffer', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.POINTER(_ctypes.c_int)], GLXPbuffer)
glXDestroyPbuffer = _get_function('glXDestroyPbuffer', [_ctypes.POINTER(Display), GLXPbuffer], None)
glXQueryDrawable = _get_function('glXQueryDrawable', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glXCreateNewContext = _get_function('glXCreateNewContext', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.c_int, GLXContext, _ctypes.c_int], GLXContext)
glXMakeContextCurrent = _get_function('glXMakeContextCurrent', [_ctypes.POINTER(Display), GLXDrawable, GLXDrawable, GLXContext], _ctypes.c_int)
glXGetCurrentReadDrawable = _get_function('glXGetCurrentReadDrawable', [], GLXDrawable)
glXQueryContext = _get_function('glXQueryContext', [_ctypes.POINTER(Display), GLXContext, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
glXSelectEvent = _get_function('glXSelectEvent', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.c_uint], None)
glXGetSelectedEvent = _get_function('glXGetSelectedEvent', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.POINTER(_ctypes.c_uint)], None)
