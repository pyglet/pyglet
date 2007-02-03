#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
from ctypes.util import find_library

from pyglet.GL.lib import missing_function

__all__ = ['link_GL', 'link_GLU']

gl_path = find_library('GL')
if not gl_path:
    raise ImportError('GL shared library not found.')
gl_lib = cdll.LoadLibrary(gl_path)

glu_path = find_library('GLU')
if not glu_path:
    # Hacky hack, unlikely to happen.
    glu_lib = gl_lib
else:
    glu_lib = cdll.LoadLibrary(glu_path)

# Look for glXGetProcAddressARB extension, use it as fallback (for
# ATI fglrx driver).
try:
    glXGetProcAddressARB = getattr(gl_lib, 'glXGetProcAddressARB')
    glXGetProcAddressARB.restype = c_void_p
    glXGetProcAddressARB.argtypes = [c_char_p]
    _have_getprocaddress = True
except AttributeError:
    _have_get_procaddress = False
    
def link_GL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(gl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError, e:
        if _have_getprocaddress:
            # Fallback if implemented but not in ABI
            addr = glXGetProcAddressARB(name)
            if addr:
                ftype = CFUNCTYPE(*((restype,) + tuple(argtypes)))
                return ftype(addr)

    return missing_function(name, requires, suggestions)

link_GLX = link_GL

def link_GLU(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(glu_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError, e:
        return missing_function(name, requires, suggestions)

