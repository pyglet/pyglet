#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
from ctypes.util import find_library

from pyglet.GL.lib import missing_function

__all__ = ['link_function']

path = find_library('GL')
if not path:
    raise ImportError('GL shared library not found.')
lib = cdll.LoadLibrary(path)

# Look for glXGetProcAddressARB extension, use it as fallback (for
# ATI fglrx driver).
try:
    glXGetProcAddressARB = getattr(lib, 'glXGetProcAddressARB')
    glXGetProcAddressARB.restype = c_void_p
    glXGetProcAddressARB.argtypes = [c_char_p]
    _have_getprocaddress = True
except AttributeError:
    _have_get_procaddress = False
    
def link_function(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(lib, name)
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

