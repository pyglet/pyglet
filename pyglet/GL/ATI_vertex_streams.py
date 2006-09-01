
"""ATI_vertex_streams
http://www.ati.com/developer/sdk/RADEONSDK/Html/Info/ATI_vertex_streams.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MAX_VERTEX_STREAMS_ATI = 0x876B
GL_VERTEX_SOURCE_ATI = 0x876C
GL_VERTEX_STREAM0_ATI = 0x876D
GL_VERTEX_STREAM1_ATI = 0x876E
GL_VERTEX_STREAM2_ATI = 0x876F
GL_VERTEX_STREAM3_ATI = 0x8770
GL_VERTEX_STREAM4_ATI = 0x8771
GL_VERTEX_STREAM5_ATI = 0x8772
GL_VERTEX_STREAM6_ATI = 0x8773
GL_VERTEX_STREAM7_ATI = 0x8774
glClientActiveVertexStreamATI = _get_function('glClientActiveVertexStreamATI', [_ctypes.c_uint], None)
glVertexBlendEnviATI = _get_function('glVertexBlendEnviATI', [_ctypes.c_uint, _ctypes.c_int], None)
glVertexBlendEnvfATI = _get_function('glVertexBlendEnvfATI', [_ctypes.c_uint, _ctypes.c_float], None)
glVertexStream2sATI = _get_function('glVertexStream2sATI', [_ctypes.c_uint, _ctypes.c_short, _ctypes.c_short], None)
glVertexStream2svATI = _get_function('glVertexStream2svATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
glVertexStream2iATI = _get_function('glVertexStream2iATI', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int], None)
glVertexStream2ivATI = _get_function('glVertexStream2ivATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glVertexStream2fATI = _get_function('glVertexStream2fATI', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float], None)
glVertexStream2fvATI = _get_function('glVertexStream2fvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glVertexStream2dATI = _get_function('glVertexStream2dATI', [_ctypes.c_uint, _ctypes.c_double, _ctypes.c_double], None)
glVertexStream2dvATI = _get_function('glVertexStream2dvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glVertexStream3sATI = _get_function('glVertexStream3sATI', [_ctypes.c_uint, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glVertexStream3svATI = _get_function('glVertexStream3svATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
glVertexStream3iATI = _get_function('glVertexStream3iATI', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glVertexStream3ivATI = _get_function('glVertexStream3ivATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glVertexStream3fATI = _get_function('glVertexStream3fATI', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glVertexStream3fvATI = _get_function('glVertexStream3fvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glVertexStream3dATI = _get_function('glVertexStream3dATI', [_ctypes.c_uint, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glVertexStream3dvATI = _get_function('glVertexStream3dvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glVertexStream4sATI = _get_function('glVertexStream4sATI', [_ctypes.c_uint, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glVertexStream4svATI = _get_function('glVertexStream4svATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
glVertexStream4iATI = _get_function('glVertexStream4iATI', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glVertexStream4ivATI = _get_function('glVertexStream4ivATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glVertexStream4fATI = _get_function('glVertexStream4fATI', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glVertexStream4fvATI = _get_function('glVertexStream4fvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glVertexStream4dATI = _get_function('glVertexStream4dATI', [_ctypes.c_uint, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glVertexStream4dvATI = _get_function('glVertexStream4dvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
glNormalStream3bATI = _get_function('glNormalStream3bATI', [_ctypes.c_uint, _ctypes.c_byte, _ctypes.c_byte, _ctypes.c_byte], None)
glNormalStream3bvATI = _get_function('glNormalStream3bvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_byte)], None)
glNormalStream3sATI = _get_function('glNormalStream3sATI', [_ctypes.c_uint, _ctypes.c_short, _ctypes.c_short, _ctypes.c_short], None)
glNormalStream3svATI = _get_function('glNormalStream3svATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_short)], None)
glNormalStream3iATI = _get_function('glNormalStream3iATI', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glNormalStream3ivATI = _get_function('glNormalStream3ivATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glNormalStream3fATI = _get_function('glNormalStream3fATI', [_ctypes.c_uint, _ctypes.c_float, _ctypes.c_float, _ctypes.c_float], None)
glNormalStream3fvATI = _get_function('glNormalStream3fvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glNormalStream3dATI = _get_function('glNormalStream3dATI', [_ctypes.c_uint, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
glNormalStream3dvATI = _get_function('glNormalStream3dvATI', [_ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
