
"""OML_sync_control
http://oss.sgi.com/projects/ogl-sample/registry/OML/glx_sync_control.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glXGetMscRateOML = _get_function('glXGetMscRateOML', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.POINTER(int32_t), _ctypes.POINTER(int32_t)], _ctypes.c_int)
glXGetSyncValuesOML = _get_function('glXGetSyncValuesOML', [_ctypes.POINTER(Display), GLXDrawable, _ctypes.POINTER(int64_t), _ctypes.POINTER(int64_t), _ctypes.POINTER(int64_t)], _ctypes.c_int)
glXSwapBuffersMscOML = _get_function('glXSwapBuffersMscOML', [_ctypes.POINTER(Display), GLXDrawable, int64_t, int64_t, int64_t], int64_t)
glXWaitForMscOML = _get_function('glXWaitForMscOML', [_ctypes.POINTER(Display), GLXDrawable, int64_t, int64_t, int64_t, _ctypes.POINTER(int64_t), _ctypes.POINTER(int64_t), _ctypes.POINTER(int64_t)], _ctypes.c_int)
glXWaitForSbcOML = _get_function('glXWaitForSbcOML', [_ctypes.POINTER(Display), GLXDrawable, int64_t, _ctypes.POINTER(int64_t), _ctypes.POINTER(int64_t), _ctypes.POINTER(int64_t)], _ctypes.c_int)
