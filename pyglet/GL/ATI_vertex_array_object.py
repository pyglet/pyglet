
"""ATI_vertex_array_object
http://oss.sgi.com/projects/ogl-sample/registry/ATI/vertex_array_object.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_STATIC_ATI = 0x8760
GL_DYNAMIC_ATI = 0x8761
GL_PRESERVE_ATI = 0x8762
GL_DISCARD_ATI = 0x8763
GL_OBJECT_BUFFER_SIZE_ATI = 0x8764
GL_OBJECT_BUFFER_USAGE_ATI = 0x8765
GL_ARRAY_OBJECT_BUFFER_ATI = 0x8766
GL_ARRAY_OBJECT_OFFSET_ATI = 0x8767
glArrayObjectATI = _get_function('glArrayObjectATI', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint], None)
glFreeObjectBufferATI = _get_function('glFreeObjectBufferATI', [_ctypes.c_uint], None)
glGetArrayObjectfvATI = _get_function('glGetArrayObjectfvATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetArrayObjectivATI = _get_function('glGetArrayObjectivATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetObjectBufferfvATI = _get_function('glGetObjectBufferfvATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetObjectBufferivATI = _get_function('glGetObjectBufferivATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetVariantArrayObjectfvATI = _get_function('glGetVariantArrayObjectfvATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetVariantArrayObjectivATI = _get_function('glGetVariantArrayObjectivATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glIsObjectBufferATI = _get_function('glIsObjectBufferATI', [_ctypes.c_uint], _ctypes.c_ubyte)
glNewObjectBufferATI = _get_function('glNewObjectBufferATI', [_ctypes.c_int, _ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_uint)
glUpdateObjectBufferATI = _get_function('glUpdateObjectBufferATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p, _ctypes.c_uint], None)
glVariantArrayObjectATI = _get_function('glVariantArrayObjectATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint], None)
