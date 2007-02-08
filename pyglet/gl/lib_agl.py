#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
from ctypes.util import find_library

from pyglet.GL.lib import missing_function

__all__ = ['link_GL', 'link_GLU', 'link_AGL']

gl_path = find_library('OpenGL')
if not gl_path:
    raise ImportError('OpenGL framework not found.')
gl_lib = cdll.LoadLibrary(gl_path)

agl_path = find_library('AGL')
if not agl_path:
    # hacky, will never happen
    agl_lib = gl_lib
else:
    agl_lib = cdll.LoadLibrary(agl_path)

def link_GL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(gl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError, e:
        return missing_function(name, requires, suggestions)

link_GLU = link_GL

def link_AGL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(agl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError, e:
        return missing_function(name, requires, suggestions)

