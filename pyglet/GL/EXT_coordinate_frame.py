
"""EXT_coordinate_frame
http://oss.sgi.com/projects/ogl-sample/registry/EXT/coordinate_frame.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TANGENT_ARRAY_EXT = 0x8439
GL_BINORMAL_ARRAY_EXT = 0x843A
GL_CURRENT_TANGENT_EXT = 0x843B
GL_CURRENT_BINORMAL_EXT = 0x843C
GL_TANGENT_ARRAY_TYPE_EXT = 0x843E
GL_TANGENT_ARRAY_STRIDE_EXT = 0x843F
GL_BINORMAL_ARRAY_TYPE_EXT = 0x8440
GL_BINORMAL_ARRAY_STRIDE_EXT = 0x8441
GL_TANGENT_ARRAY_POINTER_EXT = 0x8442
GL_BINORMAL_ARRAY_POINTER_EXT = 0x8443
GL_MAP1_TANGENT_EXT = 0x8444
GL_MAP2_TANGENT_EXT = 0x8445
GL_MAP1_BINORMAL_EXT = 0x8446
GL_MAP2_BINORMAL_EXT = 0x8447
glBinormalPointerEXT = _get_function('glBinormalPointerEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glTangentPointerEXT = _get_function('glTangentPointerEXT', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
