from ctypes import *

import pyglet.lib
from pyglet.gl.lib import missing_function, decorate_function

__all__ = ['link_GL', 'link_AGL']

gl_lib = pyglet.lib.load_library(framework='OpenGL')
agl_lib = pyglet.lib.load_library(framework='AGL')


def link_GL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(gl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        decorate_function(func, name)
        return func
    except AttributeError:
        return missing_function(name, requires, suggestions)


def link_AGL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(agl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        decorate_function(func, name)
        return func
    except AttributeError:
        return missing_function(name, requires, suggestions)
