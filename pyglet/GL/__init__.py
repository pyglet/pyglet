#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
import ctypes.util
import sys

from pyglet.GL.info import have_context

if sys.platform in ('win32', 'cygwin'):
    class WGLExtensionProxy(object):
        __slots__ = ['name', 'ftype', 'func']
        def __init__(self, name, ftype):
            self.name = name
            self.ftype = ftype
            self.func = None

        def __call__(self, *args, **kwargs):
            if self.func:
                return self.func(*args, **kwargs)

            if not have_context:
                raise Exception('Cannot call extension function before GL ' +
                    'context is created.')
            address = _WGL.wglGetProcAddress(self.name)
            if not address:
                raise Exception('Extension function "%s" not found' % self.name)
            self.func = self.ftype(address)
            return self.func(*args, **kwargs)
    
    import WGL as _WGL
    _gl = ctypes.windll.opengl32
    def get_function(name, argtypes, rtype):
        if hasattr(_gl, name):
            func = getattr(_gl, name)
            func.argtypes = argtypes
            func.restype = rtype
            return func

        # Not in opengl32.dll.  Maybe can't get pointer from WGL yet, have to
        # wait until we have a context.
        try:
            fargs = (rtype,) + tuple(argtypes)
            ftype = ctypes.WINFUNCTYPE(*fargs)
            if have_context():
                address = _WGL.wglGetProcAddress(name)
                if not address:
                    raise AttributeError, name
                return ftype.from_address(address)
            else:
                return WGLExtensionProxy(name, ftype)
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
    path = ctypes.util.find_library('GL')
    if not path:
        raise ImportError('GL shared library not found')
    _gl = ctypes.cdll.LoadLibrary(path)
    def get_function(name, argtypes, rtype):
        try:
            func = getattr(_gl, name)
            func.argtypes = argtypes
            func.restype = rtype
            return func
        except AttributeError, e:
            raise ImportError(e)
 
# No ptrdiff_t in ctypes, discover it
_int_types = (ctypes.c_int16, ctypes.c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64 defined; it's
    # a pretty good bet that these builds do not have 64-bit pointers.
    _int_types += (ctypes.c_int64,)
for t in _int_types:
    if ctypes.sizeof(t) == ctypes.sizeof(ctypes.c_size_t):
        c_ptrdiff_t = t
