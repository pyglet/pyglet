"""Cached information about version and extensions of current WGL implementation."""
from __future__ import annotations

import warnings
from ctypes import c_char_p, cast

from pyglet.graphics.api.gl import GL_EXTENSIONS, OpenGLSurfaceContext
from pyglet.graphics.api.gl.lib import MissingFunctionException
from pyglet.util import asstr


class WGLInfoException(Exception):  # noqa: N818
    pass


class WGLInfo:
    @staticmethod
    def get_extensions(ctx: OpenGLSurfaceContext) -> list[str]:
        """Can only be called when a context is in scope."""
        try:
            return asstr(ctx.platform_func.wglGetExtensionsStringEXT()).split()
        except MissingFunctionException:
            warnings.warn("Missing WGL function: wglGetExtensionsStringEXT}.")
            return asstr(cast(ctx.glGetString(GL_EXTENSIONS), c_char_p).value).split()
