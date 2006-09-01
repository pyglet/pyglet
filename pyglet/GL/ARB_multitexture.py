
"""ARB_multitexture
http://oss.sgi.com/projects/ogl-sample/registry/ARB/multitexture.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TEXTURE0_ARB = 0x84C0
GL_TEXTURE1_ARB = 0x84C1
GL_TEXTURE2_ARB = 0x84C2
GL_TEXTURE3_ARB = 0x84C3
GL_TEXTURE4_ARB = 0x84C4
GL_TEXTURE5_ARB = 0x84C5
GL_TEXTURE6_ARB = 0x84C6
GL_TEXTURE7_ARB = 0x84C7
GL_TEXTURE8_ARB = 0x84C8
GL_TEXTURE9_ARB = 0x84C9
GL_TEXTURE10_ARB = 0x84CA
GL_TEXTURE11_ARB = 0x84CB
GL_TEXTURE12_ARB = 0x84CC
GL_TEXTURE13_ARB = 0x84CD
GL_TEXTURE14_ARB = 0x84CE
GL_TEXTURE15_ARB = 0x84CF
GL_TEXTURE16_ARB = 0x84D0
GL_TEXTURE17_ARB = 0x84D1
GL_TEXTURE18_ARB = 0x84D2
GL_TEXTURE19_ARB = 0x84D3
GL_TEXTURE20_ARB = 0x84D4
GL_TEXTURE21_ARB = 0x84D5
GL_TEXTURE22_ARB = 0x84D6
GL_TEXTURE23_ARB = 0x84D7
GL_TEXTURE24_ARB = 0x84D8
GL_TEXTURE25_ARB = 0x84D9
GL_TEXTURE26_ARB = 0x84DA
GL_TEXTURE27_ARB = 0x84DB
GL_TEXTURE28_ARB = 0x84DC
GL_TEXTURE29_ARB = 0x84DD
GL_TEXTURE30_ARB = 0x84DE
GL_TEXTURE31_ARB = 0x84DF
GL_ACTIVE_TEXTURE_ARB = 0x84E0
GL_CLIENT_ACTIVE_TEXTURE_ARB = 0x84E1
GL_MAX_TEXTURE_UNITS_ARB = 0x84E2
glActiveTextureARB = _get_function('glActiveTextureARB', [_ctypes.c_uint], None)
glClientActiveTextureARB = _get_function('glClientActiveTextureARB', [_ctypes.c_uint], None)
glMultiTexCoord1dARB = _get_function('glMultiTexCoord1dARB', [_ctypes.c_uint, _ctypes.c_double], None)
glMultiTexCoord1dvARB = _get_function('glMultiTexCoord1dvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glMultiTexCoord1fARB = _get_function('glMultiTexCoord1fARB', [_ctypes.c_uint, _ctypes.c_float], None)
glMultiTexCoord1fvARB = _get_function('glMultiTexCoord1fvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glMultiTexCoord1iARB = _get_function('glMultiTexCoord1iARB', [_ctypes.c_uint, _ctypes.c_int], None)
glMultiTexCoord1ivARB = _get_function('glMultiTexCoord1ivARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glMultiTexCoord1sARB = _get_function('glMultiTexCoord1sARB', [_ctypes.c_uint, _ctypes.c_short], None)
glMultiTexCoord1svARB = _get_function('glMultiTexCoord1svARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
glMultiTexCoord2dARB = _get_function('glMultiTexCoord2dARB', [_ctypes.c_uint, _ctypes.c_double, _ctypes.c_double], None)
glMultiTexCoord2dvARB = _get_function('glMultiTexCoord2dvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glMultiTexCoord2fARB = _get_function('glMultiTexCoord2fARB', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float], None)
glMultiTexCoord2fvARB = _get_function('glMultiTexCoord2fvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glMultiTexCoord2iARB = _get_function('glMultiTexCoord2iARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int], None)
glMultiTexCoord2ivARB = _get_function('glMultiTexCoord2ivARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glMultiTexCoord2sARB = _get_function('glMultiTexCoord2sARB', [_ctypes.c_uint, _ctypes.c_short, _ctypes.c_short], None)
glMultiTexCoord2svARB = _get_function('glMultiTexCoord2svARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
glMultiTexCoord3dARB = _get_function('glMultiTexCoord3dARB', [_ctypes.c_uint, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glMultiTexCoord3dvARB = _get_function('glMultiTexCoord3dvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glMultiTexCoord3fARB = _get_function('glMultiTexCoord3fARB', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glMultiTexCoord3fvARB = _get_function('glMultiTexCoord3fvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glMultiTexCoord3iARB = _get_function('glMultiTexCoord3iARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glMultiTexCoord3ivARB = _get_function('glMultiTexCoord3ivARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glMultiTexCoord3sARB = _get_function('glMultiTexCoord3sARB', [_ctypes.c_uint, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glMultiTexCoord3svARB = _get_function('glMultiTexCoord3svARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
glMultiTexCoord4dARB = _get_function('glMultiTexCoord4dARB', [_ctypes.c_uint, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glMultiTexCoord4dvARB = _get_function('glMultiTexCoord4dvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glMultiTexCoord4fARB = _get_function('glMultiTexCoord4fARB', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glMultiTexCoord4fvARB = _get_function('glMultiTexCoord4fvARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glMultiTexCoord4iARB = _get_function('glMultiTexCoord4iARB', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glMultiTexCoord4ivARB = _get_function('glMultiTexCoord4ivARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glMultiTexCoord4sARB = _get_function('glMultiTexCoord4sARB', [_ctypes.c_uint, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glMultiTexCoord4svARB = _get_function('glMultiTexCoord4svARB', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
