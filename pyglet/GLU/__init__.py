#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
import ctypes.util
import sys

if sys.platform == 'win32':
    import pyglet.window.win32.WGL as _WGL
    _gl = ctypes.windll.opengl32
    def get_function(name, argtypes, rtype):
        if hasattr(_gl, name):
            func = getattr(_gl, name)
            func.argtypes = argtypes
            func.restype = rtype
            return func

        # Not in opengl32.dll, ask WGL for a pointer (requires context first)
        try:
            fargs = (rtype,) + tuple(argtypes)
            ftype = ctypes.CFUNCTYPE(*fargs)
            address = _WGL.wglGetProcAddress(name)
            return ftype.from_address(address)
        except AttributeError, e:
            raise ImportError(e)

elif sys.platform == 'darwin':
    path = ctypes.util.find_library('OpenGL')
    if not path:
        raise ImportError('OpenGL framework not found')
    _gl = ctypes.cdll.LoadLibrary(path)
    def get_function(name, argtypes, rtype):
        try:
            func = getattr(_gl, name)
            func.argtypes = argtypes
            func.restype = rtype
            return func
        except AttributeError, e:
            raise ImportError(e)

else:
    path = ctypes.util.find_library('GLU')
    if not path:
        raise ImportError('GLU shared library not found')
    _glu = ctypes.cdll.LoadLibrary(path)
    def get_function(name, argtypes, rtype):
        try:
            func = getattr(_glu, name)
            func.argtypes = argtypes
            func.restype = rtype
            return func
        except AttributeError, e:
            raise ImportError(e)

