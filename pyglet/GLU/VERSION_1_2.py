#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes as _ctypes
from pyglet.GLU import get_function as _get_function
from pyglet.GLU.VERSION_1_1 import *

gluNurbsCallback = _get_function('gluNurbsCallback', [_ctypes.c_void_p, _ctypes.c_uint, GLUfuncptr], None)
gluNurbsCallbackData = _get_function('gluNurbsCallbackData', [_ctypes.c_void_p, _ctypes.c_void_p], None)
