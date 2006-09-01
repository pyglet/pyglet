
"""ATI_vertex_attrib_array_object
http://oss.sgi.com/projects/ogl-sample/registry/ATI/vertex_attrib_array_object.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glGetVertexAttribArrayObjectfvATI = _get_function('glGetVertexAttribArrayObjectfvATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetVertexAttribArrayObjectivATI = _get_function('glGetVertexAttribArrayObjectivATI', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glVertexAttribArrayObjectATI = _get_function('glVertexAttribArrayObjectATI', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_ubyte, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint], None)
