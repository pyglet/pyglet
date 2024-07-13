from __future__ import annotations

import ctypes
from ctypes import CFUNCTYPE, POINTER, c_char_p, c_int, cast
from typing import Any, Callable, Sequence

import pyglet
from pyglet.gl.lib import decorate_function, missing_function
from pyglet.util import asbytes

__all__ = ['link_GL', 'link_WGL']

_debug_trace = pyglet.options['debug_trace']

gl_lib = ctypes.windll.opengl32
wgl_lib = gl_lib

if _debug_trace:
    from pyglet.lib import _TraceLibrary

    gl_lib = _TraceLibrary(gl_lib)
    wgl_lib = _TraceLibrary(wgl_lib)

try:
    wglGetProcAddress = wgl_lib.wglGetProcAddress  # noqa: N816
    wglGetProcAddress.restype = CFUNCTYPE(POINTER(c_int))
    wglGetProcAddress.argtypes = [c_char_p]
    _have_get_proc_address = True
except AttributeError:
    _have_get_proc_address = False

class_slots = ['name', 'requires', 'suggestions', 'ftype', 'func']


def makeWGLFunction(func: Callable) -> Callable:  # noqa: N802
    class WGLFunction:
        __slots__ = class_slots
        __call__ = func

    return WGLFunction


class WGLFunctionProxy:
    __slots__ = class_slots

    def __init__(self, name: str, ftype: ctypes.WINFUNCTYPE, requires: str | None,
                 suggestions: list[str] | None) -> None:
        assert _have_get_proc_address
        self.name = name
        self.ftype = ftype
        self.requires = requires
        self.suggestions = suggestions
        self.func = None

    def __call__(self, *args: Any, **kwargs: Any) -> Callable:
        from pyglet.gl import current_context
        if not current_context:
            msg = f'Call to function "{self.name}" before GL context created'
            raise Exception(msg)
        address = wglGetProcAddress(asbytes(self.name))
        if cast(address, POINTER(c_int)):  # check cast because address is func
            self.func = cast(address, self.ftype)
            decorate_function(self.func, self.name)
        else:
            self.func = missing_function(
                self.name, self.requires, self.suggestions)

        self.__class__ = makeWGLFunction(self.func)

        return self.func(*args, **kwargs)


def link_GL(name: str, restype: Any, argtypes: Any, requires: str | None = None,  # noqa: N802, D103
            suggestions: Sequence[str] | None = None) -> Callable[..., Any]:
    try:
        func = getattr(gl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        decorate_function(func, name)
        return func
    except AttributeError:
        # Not in opengl32.dll. Try and get a pointer from WGL.
        try:
            fargs = (restype,) + tuple(argtypes)
            ftype = ctypes.WINFUNCTYPE(*fargs)
            if _have_get_proc_address:
                from pyglet.gl import gl_info
                if gl_info.have_context():
                    address = wglGetProcAddress(name)
                    if address:
                        func = cast(address, ftype)
                        decorate_function(func, name)
                        return func
                else:
                    # Insert proxy until we have a context
                    return WGLFunctionProxy(name, ftype, requires, suggestions)
        except:  # noqa: E722, S110
            # TODO: Figure out what exception this can cause instead of catching all.
            pass

        return missing_function(name, requires, suggestions)


link_WGL = link_GL  # noqa: N816
