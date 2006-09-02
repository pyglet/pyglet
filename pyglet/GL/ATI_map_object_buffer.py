
"""ATI_map_object_buffer
http://www.ati.com/developer/sdk/RADEONSDK/Html/Info/ATI_map_object_buffer.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glMapObjectBufferATI = _get_function('glMapObjectBufferATI', [_ctypes.c_uint], _ctypes.c_void_p)
glUnmapObjectBufferATI = _get_function('glUnmapObjectBufferATI', [_ctypes.c_uint], None)
