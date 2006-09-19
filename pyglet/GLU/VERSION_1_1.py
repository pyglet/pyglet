#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes as _ctypes
from pyglet.GLU import get_function as _get_function
from pyglet.GLU.VERSION_1_0 import *

gluGetString = _get_function('gluGetString', [_ctypes.c_uint], _ctypes.c_char_p)
