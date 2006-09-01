
"""ARB_vertex_shader
http://oss.sgi.com/projects/ogl-sample/registry/ARB/vertex_shader.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_VERTEX_SHADER_ARB = 0x8B31
GL_MAX_VERTEX_UNIFORM_COMPONENTS_ARB = 0x8B4A
GL_MAX_VARYING_FLOATS_ARB = 0x8B4B
GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS_ARB = 0x8B4C
GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS_ARB = 0x8B4D
GL_OBJECT_ACTIVE_ATTRIBUTES_ARB = 0x8B89
GL_OBJECT_ACTIVE_ATTRIBUTE_MAX_LENGTH_ARB = 0x8B8A
glBindAttribLocationARB = _get_function('glBindAttribLocationARB', [GLhandleARB, _ctypes.c_uint, _ctypes.POINTER(GLcharARB)], None)
glGetActiveAttribARB = _get_function('glGetActiveAttribARB', [GLhandleARB, _ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_uint), _ctypes.POINTER(GLcharARB)], None)
glGetAttribLocationARB = _get_function('glGetAttribLocationARB', [GLhandleARB, _ctypes.POINTER(GLcharARB)], _ctypes.c_int)
