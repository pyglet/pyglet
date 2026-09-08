from __future__ import annotations

from ctypes import POINTER, CFUNCTYPE, c_char_p, cast
from typing import Any, Callable, Sequence

import pyglet
import pyglet.util
from pyglet.libs import missing_function


__all__ = ['link_EGL']

if pyglet.compat_platform in ("win32", "cygwin"):
    egl_lib = pyglet.lib.load_library("EGL", win32=("libEGL.dll", "EGL.dll"))
else:
    egl_lib = pyglet.lib.load_library("EGL")

# Look for eglGetProcAddress
eglGetProcAddress = getattr(egl_lib, 'eglGetProcAddress')
eglGetProcAddress.restype = POINTER(CFUNCTYPE(None))
eglGetProcAddress.argtypes = [c_char_p]


def link_EGL(name: str, restype: Any, argtypes: Any, requires: str | None = None,
             suggestions: Sequence[str] | None = None) -> Callable[..., Any]:
    try:
        func = getattr(egl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError:
        addr = eglGetProcAddress(pyglet.util.asbytes(name))
        if addr:
            ftype = CFUNCTYPE(*(restype, *tuple(argtypes)))
            func = cast(addr, ftype)
            return func

    return missing_function(name, requires, suggestions)
