
"""ARB_transpose_matrix
http://oss.sgi.com/projects/ogl-sample/registry/ARB/transpose_matrix.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_TRANSPOSE_MODELVIEW_MATRIX_ARB = 0x84E3
GL_TRANSPOSE_PROJECTION_MATRIX_ARB = 0x84E4
GL_TRANSPOSE_TEXTURE_MATRIX_ARB = 0x84E5
GL_TRANSPOSE_COLOR_MATRIX_ARB = 0x84E6
glLoadTransposeMatrixfARB = _get_function('glLoadTransposeMatrixfARB', [_ctypes.c_float], None)
glLoadTransposeMatrixdARB = _get_function('glLoadTransposeMatrixdARB', [_ctypes.c_double], None)
glMultTransposeMatrixfARB = _get_function('glMultTransposeMatrixfARB', [_ctypes.c_float], None)
glMultTransposeMatrixdARB = _get_function('glMultTransposeMatrixdARB', [_ctypes.c_double], None)
