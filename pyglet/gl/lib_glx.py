from __future__ import annotations

from ctypes import CFUNCTYPE, POINTER, c_ubyte, cast, create_string_buffer, pointer
from typing import Any, Callable, Sequence

import pyglet.lib
from pyglet.gl.lib import decorate_function, missing_function
from pyglet.util import asbytes

__all__ = ['link_GL', 'link_GLX']

gl_lib = pyglet.lib.load_library('GL')

# Look for glXGetProcAddressARB extension, use it as fallback (for ATI fglrx and DRI drivers).
try:
    glXGetProcAddressARB = getattr(gl_lib, 'glXGetProcAddressARB')  # noqa: B009, N816
    glXGetProcAddressARB.restype = POINTER(CFUNCTYPE(None))
    glXGetProcAddressARB.argtypes = [POINTER(c_ubyte)]
    _have_getprocaddress = True
except AttributeError:
    _have_getprocaddress = False


def link_GL(name: str, restype: Any, argtypes: Any, requires: str | None = None,  # noqa: N802
            suggestions: Sequence[str] | None = None) -> Callable[..., Any]:
    """Attempt to retrieve the GL function from the loaded library.

    If the function is not found, an attempt will be made via glXGetProcAddressARB.

    If both are unsuccessful, a dummy function will be returned that raises a MissingFunctionException.
    """
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
                ftype = CFUNCTYPE(*((restype, *tuple(argtypes))))
                func = cast(addr, ftype)
                decorate_function(func, name)
                return func

    return missing_function(name, requires, suggestions)


link_GLX = link_GL  # noqa: N816
