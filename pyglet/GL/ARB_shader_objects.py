
"""ARB_shader_objects
http://oss.sgi.com/projects/ogl-sample/registry/ARB/shader_objects.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PROGRAM_OBJECT_ARB = 0x8B40
GL_SHADER_OBJECT_ARB = 0x8B48
GL_OBJECT_TYPE_ARB = 0x8B4E
GL_OBJECT_SUBTYPE_ARB = 0x8B4F
GL_FLOAT_VEC2_ARB = 0x8B50
GL_FLOAT_VEC3_ARB = 0x8B51
GL_FLOAT_VEC4_ARB = 0x8B52
GL_INT_VEC2_ARB = 0x8B53
GL_INT_VEC3_ARB = 0x8B54
GL_INT_VEC4_ARB = 0x8B55
GL_BOOL_ARB = 0x8B56
GL_BOOL_VEC2_ARB = 0x8B57
GL_BOOL_VEC3_ARB = 0x8B58
GL_BOOL_VEC4_ARB = 0x8B59
GL_FLOAT_MAT2_ARB = 0x8B5A
GL_FLOAT_MAT3_ARB = 0x8B5B
GL_FLOAT_MAT4_ARB = 0x8B5C
GL_SAMPLER_1D_ARB = 0x8B5D
GL_SAMPLER_2D_ARB = 0x8B5E
GL_SAMPLER_3D_ARB = 0x8B5F
GL_SAMPLER_CUBE_ARB = 0x8B60
GL_SAMPLER_1D_SHADOW_ARB = 0x8B61
GL_SAMPLER_2D_SHADOW_ARB = 0x8B62
GL_SAMPLER_2D_RECT_ARB = 0x8B63
GL_SAMPLER_2D_RECT_SHADOW_ARB = 0x8B64
GL_OBJECT_DELETE_STATUS_ARB = 0x8B80
GL_OBJECT_COMPILE_STATUS_ARB = 0x8B81
GL_OBJECT_LINK_STATUS_ARB = 0x8B82
GL_OBJECT_VALIDATE_STATUS_ARB = 0x8B83
GL_OBJECT_INFO_LOG_LENGTH_ARB = 0x8B84
GL_OBJECT_ATTACHED_OBJECTS_ARB = 0x8B85
GL_OBJECT_ACTIVE_UNIFORMS_ARB = 0x8B86
GL_OBJECT_ACTIVE_UNIFORM_MAX_LENGTH_ARB = 0x8B87
GL_OBJECT_SHADER_SOURCE_LENGTH_ARB = 0x8B88
GLcharARB = _ctypes.c_char
GLhandleARB = unsigned int
glAttachObjectARB = _get_function('glAttachObjectARB', [GLhandleARB, GLhandleARB], None)
glCompileShaderARB = _get_function('glCompileShaderARB', [GLhandleARB], None)
glCreateProgramObjectARB = _get_function('glCreateProgramObjectARB', [], GLhandleARB)
glCreateShaderObjectARB = _get_function('glCreateShaderObjectARB', [_ctypes.c_uint], GLhandleARB)
glDeleteObjectARB = _get_function('glDeleteObjectARB', [GLhandleARB], None)
glDetachObjectARB = _get_function('glDetachObjectARB', [GLhandleARB, GLhandleARB], None)
glGetActiveUniformARB = _get_function('glGetActiveUniformARB', [GLhandleARB, _ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_uint), _ctypes.POINTER(GLcharARB)], None)
glGetAttachedObjectsARB = _get_function('glGetAttachedObjectsARB', [GLhandleARB, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(GLhandleARB)], None)
glGetHandleARB = _get_function('glGetHandleARB', [_ctypes.c_uint], GLhandleARB)
glGetInfoLogARB = _get_function('glGetInfoLogARB', [GLhandleARB, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(GLcharARB)], None)
glGetObjectParameterfvARB = _get_function('glGetObjectParameterfvARB', [GLhandleARB, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetObjectParameterivARB = _get_function('glGetObjectParameterivARB', [GLhandleARB, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetShaderSourceARB = _get_function('glGetShaderSourceARB', [GLhandleARB, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(GLcharARB)], None)
glGetUniformLocationARB = _get_function('glGetUniformLocationARB', [GLhandleARB, _ctypes.POINTER(GLcharARB)], _ctypes.c_int)
glGetUniformfvARB = _get_function('glGetUniformfvARB', [GLhandleARB, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glGetUniformivARB = _get_function('glGetUniformivARB', [GLhandleARB, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], None)
glLinkProgramARB = _get_function('glLinkProgramARB', [GLhandleARB], None)
glShaderSourceARB = _get_function('glShaderSourceARB', [GLhandleARB, _ctypes.c_int, _ctypes.POINTER(_ctypes.POINTER(GLcharARB)), _ctypes.POINTER(_ctypes.c_int)], None)
glUniform1fARB = _get_function('glUniform1fARB', [_ctypes.c_int, _ctypes.c_float], None)
glUniform1fvARB = _get_function('glUniform1fvARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glUniform1iARB = _get_function('glUniform1iARB', [_ctypes.c_int, _ctypes.c_int], None)
glUniform1ivARB = _get_function('glUniform1ivARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], None)
glUniform2fARB = _get_function('glUniform2fARB', [_ctypes.c_int, _ctypes.c_float, _ctypes.c_float], None)
glUniform2fvARB = _get_function('glUniform2fvARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glUniform2iARB = _get_function('glUniform2iARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glUniform2ivARB = _get_function('glUniform2ivARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], None)
glUniform3fARB = _get_function('glUniform3fARB', [_ctypes.c_int, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glUniform3fvARB = _get_function('glUniform3fvARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glUniform3iARB = _get_function('glUniform3iARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glUniform3ivARB = _get_function('glUniform3ivARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], None)
glUniform4fARB = _get_function('glUniform4fARB', [_ctypes.c_int, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glUniform4fvARB = _get_function('glUniform4fvARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float)], None)
glUniform4iARB = _get_function('glUniform4iARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glUniform4ivARB = _get_function('glUniform4ivARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], None)
glUniformMatrix2fvARB = _get_function('glUniformMatrix2fvARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_ubyte, _ctypes.POINTER(_ctypes.c_float)], None)
glUniformMatrix3fvARB = _get_function('glUniformMatrix3fvARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_ubyte, _ctypes.POINTER(_ctypes.c_float)], None)
glUniformMatrix4fvARB = _get_function('glUniformMatrix4fvARB', [_ctypes.c_int, _ctypes.c_int, _ctypes.c_ubyte, _ctypes.POINTER(_ctypes.c_float)], None)
glUseProgramObjectARB = _get_function('glUseProgramObjectARB', [GLhandleARB], None)
glValidateProgramARB = _get_function('glValidateProgramARB', [GLhandleARB], None)
