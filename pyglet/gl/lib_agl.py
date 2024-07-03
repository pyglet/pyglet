from __future__ import annotations

from typing import Any, Callable, Sequence

import pyglet.lib
from pyglet.gl.lib import decorate_function, missing_function

from typing import Callable

__all__ = ['link_GL', 'link_AGL']

gl_lib = pyglet.lib.load_library(framework='OpenGL')
agl_lib = pyglet.lib.load_library(framework='AGL')


def link_GL(name: str, restype: Any, argtypes: Any, requires: str | None = None,  # noqa: N802, D103
            suggestions: Sequence[str] | None = None) -> Callable[..., Any]:
    try:
        func = getattr(gl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        decorate_function(func, name)
        return func
    except AttributeError:
        return missing_function(name, requires, suggestions)


def link_AGL(name: str, restype: Any, argtypes: Any, requires: str | None = None,  # noqa: N802, D103
            suggestions: Sequence[str] | None = None) -> Callable[..., Any]:
    try:
        func = getattr(agl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        decorate_function(func, name)
        return func
    except AttributeError:
        return missing_function(name, requires, suggestions)
