"""Cached information about version and extensions of current WGL implementation."""
from __future__ import annotations

import warnings
from ctypes import c_char_p, cast

from pyglet.gl import gl_info
from pyglet.gl.gl import GL_EXTENSIONS, glGetString
from pyglet.gl.lib import MissingFunctionException
from pyglet.gl.wglext_arb import wglGetExtensionsStringEXT
from pyglet.util import asstr


class WGLInfoException(Exception):  # noqa: D101, N818
    pass


class WGLInfo:  # noqa: D101
    def get_extensions(self) -> list[str]:
        if not gl_info.have_context():
            warnings.warn("Can't query WGL until a context is created.")
            return []

        try:
            return asstr(wglGetExtensionsStringEXT()).split()
        except MissingFunctionException:
            return asstr(cast(glGetString(GL_EXTENSIONS), c_char_p).value).split()

    def have_extension(self, extension: str) -> bool:
        return extension in self.get_extensions()


_wgl_info = WGLInfo()

get_extensions = _wgl_info.get_extensions
have_extension = _wgl_info.have_extension
