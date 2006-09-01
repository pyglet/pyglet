#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

try:
    # For OpenGL-ctypes
    from OpenGL import platform
    _gl = _platform.OpenGL
except ImportError:
    # For PyOpenGL
    _gl = cdll.LoadLibrary('libGL.so')

GL_QUERY_COUNTER_BITS             = 0x8864
GL_CURRENT_QUERY                  = 0x8865
GL_QUERY_RESULT                   = 0x8866
GL_QUERY_RESULT_AVAILABLE         = 0x8867
GL_SAMPLES_PASSED                 = 0x8914

glGenQueries = _gl.glGenQueries
glGenQueries.argtypes = [c_int, POINTER(c_uint)]

glIsQuery = _gl.glIsQuery
glIsQuery.argtypes = [c_uint]

glBeginQuery = _gl.glBeginQuery
glBeginQuery.argtypes = [c_int, c_uint]
glEndQuery = _gl.glEndQuery
glEndQuery.argtypes = [c_int]

glGetQueryObjectiv = _gl.glGetQueryObjectiv
glGetQueryObjectiv.argtypes = [c_uint, c_int, POINTER(c_int)]
glGetQueryObjectuiv = _gl.glGetQueryObjectuiv
glGetQueryObjectuiv.argtypes = [c_uint, c_int, POINTER(c_uint)]

glDeleteQueries = _gl.glDeleteQueries
glDeleteQueries.argtypes = [c_int, POINTER(c_uint)]
