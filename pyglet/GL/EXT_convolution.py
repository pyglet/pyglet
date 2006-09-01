
"""EXT_convolution
http://oss.sgi.com/projects/ogl-sample/registry/EXT/convolution.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_CONVOLUTION_1D_EXT = 0x8010
GL_CONVOLUTION_2D_EXT = 0x8011
GL_SEPARABLE_2D_EXT = 0x8012
GL_CONVOLUTION_BORDER_MODE_EXT = 0x8013
GL_CONVOLUTION_FILTER_SCALE_EXT = 0x8014
GL_CONVOLUTION_FILTER_BIAS_EXT = 0x8015
GL_REDUCE_EXT = 0x8016
GL_CONVOLUTION_FORMAT_EXT = 0x8017
GL_CONVOLUTION_WIDTH_EXT = 0x8018
GL_CONVOLUTION_HEIGHT_EXT = 0x8019
GL_MAX_CONVOLUTION_WIDTH_EXT = 0x801A
GL_MAX_CONVOLUTION_HEIGHT_EXT = 0x801B
GL_POST_CONVOLUTION_RED_SCALE_EXT = 0x801C
GL_POST_CONVOLUTION_GREEN_SCALE_EXT = 0x801D
GL_POST_CONVOLUTION_BLUE_SCALE_EXT = 0x801E
GL_POST_CONVOLUTION_ALPHA_SCALE_EXT = 0x801F
GL_POST_CONVOLUTION_RED_BIAS_EXT = 0x8020
GL_POST_CONVOLUTION_GREEN_BIAS_EXT = 0x8021
GL_POST_CONVOLUTION_BLUE_BIAS_EXT = 0x8022
GL_POST_CONVOLUTION_ALPHA_BIAS_EXT = 0x8023
glConvolutionFilter1DEXT = _get_function('glConvolutionFilter1DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glConvolutionFilter2DEXT = _get_function('glConvolutionFilter2DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glConvolutionParameterfEXT = _get_function('glConvolutionParameterfEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_float], None)
glConvolutionParameterfvEXT = _get_function('glConvolutionParameterfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glConvolutionParameteriEXT = _get_function('glConvolutionParameteriEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glConvolutionParameterivEXT = _get_function('glConvolutionParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glCopyConvolutionFilter1DEXT = _get_function('glCopyConvolutionFilter1DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glCopyConvolutionFilter2DEXT = _get_function('glCopyConvolutionFilter2DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], None)
glGetConvolutionFilterEXT = _get_function('glGetConvolutionFilterEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], None)
glGetConvolutionParameterfvEXT = _get_function('glGetConvolutionParameterfvEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetConvolutionParameterivEXT = _get_function('glGetConvolutionParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetSeparableFilterEXT = _get_function('glGetSeparableFilterEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p, _ctypes.c_void_p, _ctypes.c_void_p], None)
glSeparableFilter2DEXT = _get_function('glSeparableFilter2DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p, _ctypes.c_void_p], None)
