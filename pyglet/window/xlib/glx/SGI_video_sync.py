
"""SGI_video_sync
http://oss.sgi.com/projects/ogl-sample/registry/SGI/video_sync.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXGetVideoSyncSGI = _get_function('glXGetVideoSyncSGI', [_ctypes.POINTER(uint)], _ctypes.c_int)
glXWaitVideoSyncSGI = _get_function('glXWaitVideoSyncSGI', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], _ctypes.c_int)
