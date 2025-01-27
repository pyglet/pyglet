"""Cached information about version and extensions of current WGL implementation."""
from __future__ import annotations

import warnings
from ctypes import c_char_p, cast

from pyglet.graphics.api.gl import GL_EXTENSIONS, glGetString
from pyglet.graphics.api.gl.lib import MissingFunctionException
from pyglet.graphics.api.gl.win32.wglext_arb import wglGetExtensionsStringEXT
from pyglet.util import asstr


class WGLInfoException(Exception):  # noqa: N818
    pass


class WGLInfo:
    @staticmethod
    def get_extensions() -> list[str]:
        """Can only be called when a context is in scope."""
        try:
            return asstr(wglGetExtensionsStringEXT()).split()
        except MissingFunctionException:
            warnings.warn("Missing WGL function: wglGetExtensionsStringEXT}.")
            return asstr(cast(glGetString(GL_EXTENSIONS), c_char_p).value).split()
