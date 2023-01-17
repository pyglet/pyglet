from ctypes import *
from typing import Any, Callable

import pyglet.lib
from pyglet.gl.lib import missing_function, decorate_function

from pyglet.util import asbytes

__all__ = ['link_GL', 'link_GLX']

gl_lib = pyglet.lib.load_library('GL')

# Look for glXGetProcAddressARB extension, use it as fallback (for ATI fglrx and DRI drivers).
try:
    glXGetProcAddressARB = getattr(gl_lib, 'glXGetProcAddressARB')
    glXGetProcAddressARB.restype = POINTER(CFUNCTYPE(None))
    glXGetProcAddressARB.argtypes = [POINTER(c_ubyte)]
    _have_getprocaddress = True
except AttributeError:
    _have_getprocaddress = False


def link_GL(name, restype, argtypes, requires=None, suggestions=None) -> Callable[..., Any]:
    try:
        func = getattr(gl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        decorate_function(func, name)
        return func
    except AttributeError:
        if _have_getprocaddress:
            # Fallback if implemented but not in ABI
            bname = cast(pointer(create_string_buffer(asbytes(name))), POINTER(c_ubyte))
            addr = glXGetProcAddressARB(bname)
            if addr:
                ftype = CFUNCTYPE(*((restype,) + tuple(argtypes)))
                func = cast(addr, ftype)
                decorate_function(func, name)
                return func

    return missing_function(name, requires, suggestions)


link_GLX = link_GL
