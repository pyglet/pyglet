
"""ARB_vertex_buffer_object
http://oss.sgi.com/projects/ogl-sample/registry/ARB/vertex_buffer_object.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_BUFFER_SIZE_ARB = 0x8764
GL_BUFFER_USAGE_ARB = 0x8765
GL_ARRAY_BUFFER_ARB = 0x8892
GL_ELEMENT_ARRAY_BUFFER_ARB = 0x8893
GL_ARRAY_BUFFER_BINDING_ARB = 0x8894
GL_ELEMENT_ARRAY_BUFFER_BINDING_ARB = 0x8895
GL_VERTEX_ARRAY_BUFFER_BINDING_ARB = 0x8896
GL_NORMAL_ARRAY_BUFFER_BINDING_ARB = 0x8897
GL_COLOR_ARRAY_BUFFER_BINDING_ARB = 0x8898
GL_INDEX_ARRAY_BUFFER_BINDING_ARB = 0x8899
GL_TEXTURE_COORD_ARRAY_BUFFER_BINDING_ARB = 0x889A
GL_EDGE_FLAG_ARRAY_BUFFER_BINDING_ARB = 0x889B
GL_SECONDARY_COLOR_ARRAY_BUFFER_BINDING_ARB = 0x889C
GL_FOG_COORDINATE_ARRAY_BUFFER_BINDING_ARB = 0x889D
GL_WEIGHT_ARRAY_BUFFER_BINDING_ARB = 0x889E
GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING_ARB = 0x889F
GL_READ_ONLY_ARB = 0x88B8
GL_WRITE_ONLY_ARB = 0x88B9
GL_READ_WRITE_ARB = 0x88BA
GL_BUFFER_ACCESS_ARB = 0x88BB
GL_BUFFER_MAPPED_ARB = 0x88BC
GL_BUFFER_MAP_POINTER_ARB = 0x88BD
GL_STREAM_DRAW_ARB = 0x88E0
GL_STREAM_READ_ARB = 0x88E1
GL_STREAM_COPY_ARB = 0x88E2
GL_STATIC_DRAW_ARB = 0x88E4
GL_STATIC_READ_ARB = 0x88E5
GL_STATIC_COPY_ARB = 0x88E6
GL_DYNAMIC_DRAW_ARB = 0x88E8
GL_DYNAMIC_READ_ARB = 0x88E9
GL_DYNAMIC_COPY_ARB = 0x88EA
GLsizeiptrARB = _c_ptrdiff_t
GLintptrARB = _c_ptrdiff_t
glBindBufferARB = _get_function('glBindBufferARB', [_ctypes.c_uint, _ctypes.c_uint], None)
glBufferDataARB = _get_function('glBufferDataARB', [_ctypes.c_uint, GLsizeiptrARB, _ctypes.c_void_p, _ctypes.c_uint], None)
glBufferSubDataARB = _get_function('glBufferSubDataARB', [_ctypes.c_uint, GLintptrARB, GLsizeiptrARB, _ctypes.c_void_p], None)
glDeleteBuffersARB = _get_function('glDeleteBuffersARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGenBuffersARB = _get_function('glGenBuffersARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGetBufferParameterivARB = _get_function('glGetBufferParameterivARB', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetBufferPointervARB = _get_function('glGetBufferPointervARB', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p)], None)
glGetBufferSubDataARB = _get_function('glGetBufferSubDataARB', [_ctypes.c_uint, GLintptrARB, GLsizeiptrARB, _ctypes.c_void_p], None)
glIsBufferARB = _get_function('glIsBufferARB', [_ctypes.c_uint], _ctypes.c_ubyte)
glMapBufferARB = _get_function('glMapBufferARB', [_ctypes.c_uint, _ctypes.c_uint], _ctypes.c_void_p)
glUnmapBufferARB = _get_function('glUnmapBufferARB', [_ctypes.c_uint], _ctypes.c_ubyte)
