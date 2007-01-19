
"""SGIX_pbuffer
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/pbuffer.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GLX_FRONT_LEFT_BUFFER_BIT_SGIX = 0x00000001
GLX_FRONT_RIGHT_BUFFER_BIT_SGIX = 0x00000002
GLX_PBUFFER_BIT_SGIX = 0x00000004
GLX_BACK_LEFT_BUFFER_BIT_SGIX = 0x00000004
GLX_BACK_RIGHT_BUFFER_BIT_SGIX = 0x00000008
GLX_AUX_BUFFERS_BIT_SGIX = 0x00000010
GLX_DEPTH_BUFFER_BIT_SGIX = 0x00000020
GLX_STENCIL_BUFFER_BIT_SGIX = 0x00000040
GLX_ACCUM_BUFFER_BIT_SGIX = 0x00000080
GLX_SAMPLE_BUFFERS_BIT_SGIX = 0x00000100
GLX_MAX_PBUFFER_WIDTH_SGIX = 0x8016
GLX_MAX_PBUFFER_HEIGHT_SGIX = 0x8017
GLX_MAX_PBUFFER_PIXELS_SGIX = 0x8018
GLX_OPTIMAL_PBUFFER_WIDTH_SGIX = 0x8019
GLX_OPTIMAL_PBUFFER_HEIGHT_SGIX = 0x801A
GLX_PRESERVED_CONTENTS_SGIX = 0x801B
GLX_LARGEST_PBUFFER_SGIX = 0x801C
GLX_WIDTH_SGIX = 0x801D
GLX_HEIGHT_SGIX = 0x801E
GLX_EVENT_MASK_SGIX = 0x801F
GLX_DAMAGED_SGIX = 0x8020
GLX_SAVED_SGIX = 0x8021
GLX_WINDOW_SGIX = 0x8022
GLX_PBUFFER_SGIX = 0x8023
GLX_BUFFER_CLOBBER_MASK_SGIX = 0x08000000
GLXPbufferSGIX = _ctypes.c_ulong
glXCreateGLXPbufferSGIX = _get_function('glXCreateGLXPbufferSGIX', [_ctypes.POINTER(Display), GLXFBConfig, _ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], GLXPbuffer)
glXDestroyGLXPbufferSGIX = _get_function('glXDestroyGLXPbufferSGIX', [_ctypes.POINTER(Display), GLXPbuffer], None)
glXGetSelectedEventSGIX = _get_function('glXGetSelectedEventSGIX', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.POINTER(_ctypes.c_uint)], None)
glXQueryGLXPbufferSGIX = _get_function('glXQueryGLXPbufferSGIX', [_ctypes.POINTER(Display), GLXPbuffer, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glXSelectEventSGIX = _get_function('glXSelectEventSGIX', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.c_uint], None)
