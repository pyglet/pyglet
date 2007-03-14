#!/usr/bin/env python

'''Cached information about version and extensions of current WGL
implementation.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: glx_info.py 615 2007-02-07 13:17:05Z Alex.Holkner $'

from ctypes import *
import warnings

from pyglet.gl.lib import MissingFunctionException
from pyglet.gl.gl import *
from pyglet.gl.gl_info import *
from pyglet.gl.wgl import *
from pyglet.gl.wglext_abi import *

class WGLInfoException(Exception):
    pass

class WGLInfo(object):
    def get_extensions(self):
        if not gl_info.have_context:
            warnings.warn("Can't query WGL until a context is created.")
            return []

        try:
            return wglGetExtensionsStringEXT().split()
        except MissingFunctionException:
            return cast(glGetString(GL_EXTENSIONS), c_char_p).value.split()

    def have_extension(self, extension):
        return extension in self.get_extensions()

_wgl_info = WGLInfo()

get_extensions = _wgl_info.get_extensions
have_extension = _wgl_info.have_extension
