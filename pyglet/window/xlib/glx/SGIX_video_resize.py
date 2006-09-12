
"""SGIX_video_resize
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/video_resize.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GLX_SYNC_FRAME_SGIX = 0x00000000
GLX_SYNC_SWAP_SGIX = 0x00000001
glXBindChannelToWindowSGIX = _get_function('glXBindChannelToWindowSGIX', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.c_int, _ctypes.c_ulong], _ctypes.c_int)
glXChannelRectSGIX = _get_function('glXChannelRectSGIX', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], _ctypes.c_int)
glXChannelRectSyncSGIX = _get_function('glXChannelRectSyncSGIX', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint], _ctypes.c_int)
glXQueryChannelDeltasSGIX = _get_function('glXQueryChannelDeltasSGIX', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
glXQueryChannelRectSGIX = _get_function('glXQueryChannelRectSGIX', [_ctypes.POINTER(Display), _ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
