
"""ARB_matrix_palette
http://oss.sgi.com/projects/ogl-sample/registry/ARB/matrix_palette.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_MATRIX_PALETTE_ARB = 0x8840
GL_MAX_MATRIX_PALETTE_STACK_DEPTH_ARB = 0x8841
GL_MAX_PALETTE_MATRICES_ARB = 0x8842
GL_CURRENT_PALETTE_MATRIX_ARB = 0x8843
GL_MATRIX_INDEX_ARRAY_ARB = 0x8844
GL_CURRENT_MATRIX_INDEX_ARB = 0x8845
GL_MATRIX_INDEX_ARRAY_SIZE_ARB = 0x8846
GL_MATRIX_INDEX_ARRAY_TYPE_ARB = 0x8847
GL_MATRIX_INDEX_ARRAY_STRIDE_ARB = 0x8848
GL_MATRIX_INDEX_ARRAY_POINTER_ARB = 0x8849
glCurrentPaletteMatrixARB = _get_function('glCurrentPaletteMatrixARB', [_ctypes.c_int], None)
glMatrixIndexPointerARB = _get_function('glMatrixIndexPointerARB', [_ctypes.c_int, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_void_p], None)
glMatrixIndexubvARB = _get_function('glMatrixIndexubvARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_ubyte)], None)
glMatrixIndexusvARB = _get_function('glMatrixIndexusvARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_ushort)], None)
glMatrixIndexuivARB = _get_function('glMatrixIndexuivARB', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
