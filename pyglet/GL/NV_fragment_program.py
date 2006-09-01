
"""NV_fragment_program
http://oss.sgi.com/projects/ogl-sample/registry/NV/fragment_program.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MAX_FRAGMENT_PROGRAM_LOCAL_PARAMETERS_NV = 0x8868
GL_FRAGMENT_PROGRAM_NV = 0x8870
GL_MAX_TEXTURE_COORDS_NV = 0x8871
GL_MAX_TEXTURE_IMAGE_UNITS_NV = 0x8872
GL_FRAGMENT_PROGRAM_BINDING_NV = 0x8873
GL_PROGRAM_ERROR_STRING_NV = 0x8874
glGetProgramNamedParameterdvNV = _get_function('glGetProgramNamedParameterdvNV', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_ubyte), _ctypes.POINTER(_ctypes.c_double)], None)
glGetProgramNamedParameterfvNV = _get_function('glGetProgramNamedParameterfvNV', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_ubyte), _ctypes.POINTER(_ctypes.c_float)], None)
glProgramNamedParameter4dNV = _get_function('glProgramNamedParameter4dNV', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_ubyte), _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glProgramNamedParameter4dvNV = _get_function('glProgramNamedParameter4dvNV', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_ubyte), _ctypes.c_double], None)
glProgramNamedParameter4fNV = _get_function('glProgramNamedParameter4fNV', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_ubyte), _ctypes.c_float, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glProgramNamedParameter4fvNV = _get_function('glProgramNamedParameter4fvNV', [_ctypes.c_uint, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_ubyte), _ctypes.c_float], None)
