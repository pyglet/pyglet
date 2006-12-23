'''XXX hand-coded from

http://oss.sgi.com/projects/ogl-sample/registry/EXT/wgl_swap_control.txt
'''

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
wglSwapIntervalEXT = _get_function('wglSwapIntervalEXT', [_ctypes.c_int], _ctypes.c_int)
wglGetSwapIntervalEXT = _get_function('wglGetSwapIntervalEXT', [], _ctypes.c_int)
