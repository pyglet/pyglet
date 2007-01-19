#!/usr/bin/env python

'''VERSION_1_0
/usr/include/GL/glx.h
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
from pyglet.window.xlib.types import XVisualInfo, Display

GLXBadContext = 0
GLXBadContextState = 1
GLXBadDrawable = 2
GLXBadPixmap = 3
GLXBadContextTag = 4
GLXBadCurrentWindow = 5
GLXBadRenderRequest = 6
GLXBadLargeRequest = 7
GLXUnsupportedPrivateRequest = 8
GLXBadFBConfig = 9
GLXBadPbuffer = 10
GLXBadCurrentDrawable = 11
GLXBadWindow = 12

GLX_USE_GL = 1
GLX_BUFFER_SIZE = 2
GLX_LEVEL = 3
GLX_RGBA = 4
GLX_DOUBLEBUFFER = 5
GLX_STEREO = 6
GLX_AUX_BUFFERS = 7
GLX_RED_SIZE = 8
GLX_GREEN_SIZE = 9
GLX_BLUE_SIZE = 10
GLX_ALPHA_SIZE = 11
GLX_DEPTH_SIZE = 12
GLX_STENCIL_SIZE = 13
GLX_ACCUM_RED_SIZE = 14
GLX_ACCUM_GREEN_SIZE = 15
GLX_ACCUM_BLUE_SIZE = 16
GLX_ACCUM_ALPHA_SIZE = 17
GLX_BAD_SCREEN = 1
GLX_BAD_ATTRIBUTE = 2
GLX_NO_EXTENSION = 3
GLX_BAD_VISUAL = 4
GLX_BAD_CONTEXT = 5
GLX_BAD_VALUE = 6
GLX_BAD_ENUM = 7
GLX_VENDOR = 0x1
GLX_VERSION = 0x2
GLX_EXTENSIONS = 0x3
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

GLXContextID = _ctypes.c_ulong
GLXPixmap = _ctypes.c_ulong
GLXDrawable = _ctypes.c_ulong
GLXPbuffer = _ctypes.c_ulong
GLXWindow = _ctypes.c_ulong
GLXFBConfigID = _ctypes.c_ulong
GLXContext = _ctypes.c_void_p
GLXFBConfig = _ctypes.c_void_p

glXChooseVisual = _get_function('glXChooseVisual', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.POINTER(XVisualInfo))
glXCopyContext = _get_function('glXCopyContext', [_ctypes.POINTER(Display), GLXContext, GLXContext, _ctypes.c_uint], None)
glXCreateContext = _get_function('glXCreateContext', [_ctypes.POINTER(Display), _ctypes.POINTER(XVisualInfo), GLXContext, _ctypes.c_int], GLXContext)
glXCreateGLXPixmap = _get_function('glXCreateGLXPixmap', [_ctypes.POINTER(Display), _ctypes.POINTER(XVisualInfo), _ctypes.c_ulong], GLXPixmap)
glXDestroyContext = _get_function('glXDestroyContext', [_ctypes.POINTER(Display), GLXContext], None)
glXDestroyGLXPixmap = _get_function('glXDestroyGLXPixmap', [_ctypes.POINTER(Display), GLXPixmap], None)
glXGetConfig = _get_function('glXGetConfig', [_ctypes.POINTER(Display), _ctypes.POINTER(XVisualInfo), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
glXGetCurrentContext = _get_function('glXGetCurrentContext', [], GLXContext)
glXGetCurrentDrawable = _get_function('glXGetCurrentDrawable', [], GLXDrawable)
glXIsDirect = _get_function('glXIsDirect', [_ctypes.POINTER(Display), GLXContext], _ctypes.c_int)
glXMakeCurrent = _get_function('glXMakeCurrent', [_ctypes.POINTER(Display), GLXDrawable, GLXContext], _ctypes.c_int)
glXQueryExtension = _get_function('glXQueryExtension', [_ctypes.POINTER(Display), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
glXQueryVersion = _get_function('glXQueryVersion', [_ctypes.POINTER(Display), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
glXSwapBuffers = _get_function('glXSwapBuffers', [_ctypes.POINTER(Display), GLXDrawable], None)
glXUseXFont = _get_function('glXUseXFont', [_ctypes.c_ulong, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glXWaitGL = _get_function('glXWaitGL', [], None)
glXWaitX = _get_function('glXWaitX', [], None)
