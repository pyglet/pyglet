
"""APPLE_element_array
http://oss.sgi.com/projects/ogl-sample/registry/APPLE/element_array.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_ELEMENT_ARRAY_APPLE = 0x8768
GL_ELEMENT_ARRAY_TYPE_APPLE = 0x8769
GL_ELEMENT_ARRAY_POINTER_APPLE = 0x876A
glDrawElementArrayAPPLE = _get_function('glDrawElementArrayAPPLE', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int], None)
glDrawRangeElementArrayAPPLE = _get_function('glDrawRangeElementArrayAPPLE', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int], None)
glElementPointerAPPLE = _get_function('glElementPointerAPPLE', [_ctypes.c_uint, _ctypes.c_void_p], None)
glMultiDrawElementArrayAPPLE = _get_function('glMultiDrawElementArrayAPPLE', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.c_int], None)
glMultiDrawRangeElementArrayAPPLE = _get_function('glMultiDrawRangeElementArrayAPPLE', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.c_int], None)
