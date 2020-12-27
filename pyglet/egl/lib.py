from ctypes import *

import pyglet.lib
from pyglet.gl.lib import missing_function

from pyglet.util import asbytes

__all__ = ['link_EGL']

egl_lib = pyglet.lib.load_library('EGL')

# Look for eglGetProcAddress
eglGetProcAddress = getattr(egl_lib, 'eglGetProcAddress')
eglGetProcAddress.restype = POINTER(CFUNCTYPE(None))
eglGetProcAddress.argtypes = [POINTER(c_ubyte)]


def link_EGL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(egl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError:
        bname = cast(pointer(create_string_buffer(asbytes(name))), POINTER(c_ubyte))
        addr = eglGetProcAddress(bname)
        if addr:
            ftype = CFUNCTYPE(*((restype,) + tuple(argtypes)))
            func = cast(addr, ftype)
            return func

    return missing_function(name, requires, suggestions)
