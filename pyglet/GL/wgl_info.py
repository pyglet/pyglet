#!/usr/bin/env python

'''Cached information about version and extensions of current WGL
implementation.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: glx_info.py 615 2007-02-07 13:17:05Z Alex.Holkner $'

from ctypes import *
import warnings

from pyglet.GL.lib import MissingFunctionException
from pyglet.GL.info import have_context
from pyglet.GL.gl import *
from pyglet.GL.wgl import *
from pyglet.GL.wglext_abi import *

__all__ = ['WGLInfo', 'wgl_info']

class WGLInfoException(Exception):
    pass

class WGLInfo(object):
    def get_extensions(self):
        if not have_context():
            warnings.warn("Can't query WGL until a context is created.")
            return []

        try:
            return wglGetExtensionsStringEXT().split()
        except MissingFunctionException:
            return cast(glGetString(GL_EXTENSIONS), c_char_p).value.split()

    def have_extension(self, extension):
        return extension in self.get_extensions()

wgl_info = WGLInfo()

def get_wgl_extensions():
    return wgl_info.get_extensions()

def have_wgl_extension(extension):
    return wgl_info.have_extension(extension)
