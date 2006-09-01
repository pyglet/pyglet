
"""ATI_element_array
http://oss.sgi.com/projects/ogl-sample/registry/ATI/element_array.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_ELEMENT_ARRAY_ATI = 0x8768
GL_ELEMENT_ARRAY_TYPE_ATI = 0x8769
GL_ELEMENT_ARRAY_POINTER_ATI = 0x876A
glDrawElementArrayATI = _get_function('glDrawElementArrayATI', [_ctypes.c_uint, _ctypes.c_int], None)
glDrawRangeElementArrayATI = _get_function('glDrawRangeElementArrayATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glElementPointerATI = _get_function('glElementPointerATI', [_ctypes.c_uint, _ctypes.c_void_p], None)
