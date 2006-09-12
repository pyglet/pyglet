#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes as _ctypes
from pyglet.window.carbon.agl.VERSION_10_0 import *
from pyglet.window.carbon.agl.VERSION_10_0 import _get_function

aglSurfaceTexture = _get_function('aglSurfaceTexture', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)

