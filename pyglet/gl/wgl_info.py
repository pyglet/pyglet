"""Cached information about version and extensions of current WGL
implementation.
"""

from ctypes import *
import warnings

from pyglet.gl.lib import MissingFunctionException
from pyglet.gl.gl import *
from pyglet.gl import gl_info
from pyglet.gl.wgl import *
from pyglet.gl.wglext_arb import *
from pyglet.util import asstr


class WGLInfoException(Exception):
    pass


class WGLInfo:
    def get_extensions(self):
        if not gl_info.have_context():
            warnings.warn("Can't query WGL until a context is created.")
            return []

        try:
            return asstr(wglGetExtensionsStringEXT()).split()
        except MissingFunctionException:
            return asstr(cast(glGetString(GL_EXTENSIONS), c_char_p).value).split()

    def have_extension(self, extension):
        return extension in self.get_extensions()


_wgl_info = WGLInfo()

get_extensions = _wgl_info.get_extensions
have_extension = _wgl_info.have_extension
