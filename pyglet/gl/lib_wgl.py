#!/usr/bin/python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: lib_glx.py 597 2007-02-03 16:13:07Z Alex.Holkner $'

import ctypes
from ctypes import *
from ctypes.util import find_library

from pyglet.gl.lib import missing_function

__all__ = ['link_GL', 'link_GLU', 'link_WGL']

gl_lib = ctypes.windll.opengl32
glu_lib = ctypes.windll.glu32
wgl_lib = gl_lib

try:
    wglGetProcAddress = wgl_lib.wglGetProcAddress
    wglGetProcAddress.restype = CFUNCTYPE(POINTER(c_int))
    wglGetProcAddress.argtypes = [c_char_p]
    _have_get_proc_address = True
except AttributeError:
    _have_get_proc_address = False

class WGLFunctionProxy(object):
    __slots__ = ['name', 'requires', 'suggestions', 'ftype', 'func']
    def __init__(self, name, ftype, requires, suggestions):
        assert _have_get_proc_address
        self.name = name
        self.ftype = ftype
        self.requires = requires
        self.suggestions = suggestions
        self.func = None

    def __call__(self, *args, **kwargs):
        if self.func:
            return self.func(*args, **kwargs)

        from pyglet.gl.gl_info import gl_info
        if not gl_info.have_context:
            raise Exception(
                'Call to function "%s" before GL context created' % self.name)
        address = wglGetProcAddress(self.name)
        if address:
            self.func = cast(address, self.ftype)
        else:
            self.func = missing_function(
                self.name, self.requires, self.suggestions)
        result = self.func(*args, **kwargs) 
        return result

def link_GL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(gl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError, e:
        # Not in opengl32.dll. Try and get a pointer from WGL.
        try:
            fargs = (restype,) + tuple(argtypes)
            ftype = ctypes.WINFUNCTYPE(*fargs)
            if _have_get_proc_address:
                from pyglet.gl.gl_info import gl_info
                if gl_info.have_context:
                    address = wglGetProcAddress(name)
                    if address:
                        return cast(address, ftype)
                else:
                    # Insert proxy until we have a context
                    return WGLFunctionProxy(name, ftype, requires, suggestions)
        except:
            pass

        return missing_function(name, requires, suggestions)

def link_GLU(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(glu_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError, e:
        # Not in glu32.dll. Try and get a pointer from WGL.
        try:
            fargs = (restype,) + tuple(argtypes)
            ftype = ctypes.WINFUNCTYPE(*fargs)
            if _have_get_proc_address:
                from pyglet.gl.gl_info import gl_info
                if gl_info.have_context:
                    address = wglGetProcAddress(name)
                    if address:
                        return cast(address, ftype)
                else:
                    # Insert proxy until we have a context
                    return WGLFunctionProxy(name, ftype, requires, suggestions)
        except:
            pass

        return missing_function(name, requires, suggestions)

link_WGL = link_GL
