#!/usr/bin/python
# $Id:$

import warnings

from pyglet.window import *
from pyglet.GL import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GL.WGL.EXT_extensions_string import *

def have_wgl_extension(extension):
    if not get_current_context():
        warnings.warn('No GL context is set')
        return False
    
    try:
        extensions = wglGetExtensionsStringEXT()
    except GLUnsupportedExtensionException:
        extensions = glGetString(GL_EXTENSIONS)
    return extension in extensions.split()

