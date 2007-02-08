#!/usr/bin/env python

'''Information about version and extensions of current GLX implementation.

Usage::

    from pyglet.gl.glx_info import *

    if glx_info.have_extension('GLX_NV_float_buffer'):
        # ...

Or, if using more than one display::

    import pyglet.gl.glx_info

    info = GLXInfo(window._display)
    if info.get_server_vendor() == 'ATI':
        # ...

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.GL.glx import *
from pyglet.GL.glx import Display

__all__ = ['GLXInfo', 'glx_info']

class GLXInfoException(Exception):
    pass

class GLXInfo(object):
    def __init__(self, display):
        self.display = cast(pointer(display), POINTER(Display))

    def have_version(self, major, minor=0):
        if not glXQueryExtension(self.display, None, None):
            raise GLXInfoException('pyglet requires an X server with GLX')

        server = [int(i) for i in self.get_server_version().split('.')]
        client = [int(i) for i in self.get_client_version().split('.')]
        return (tuple(server) >= (major, minor) and 
                tuple(client) >= (major, minor))

    def get_server_vendor(self):
        return glXQueryServerString(self.display, 0, GLX_VENDOR)
    
    def get_server_version(self):
        # glXQueryServerString was introduced in GLX 1.1, so we need to use the
        # 1.0 function here which queries the server implementation for its
        # version.
        major = c_int()
        minor = c_int()
        if not glXQueryVersion(self.display, byref(major), byref(minor)):
            raise GLXInfoException('Could not determine GLX server version')
        return '%s.%s'%(major.value, minor.value)

    def get_server_extensions(self):
        return glXQueryServerString(self.display, 0, GLX_EXTENSIONS).split()

    def get_client_vendor(self):
        return glXGetClientString(self.display, GLX_VENDOR)

    def get_client_version(self):
        return glXGetClientString(self.display, GLX_VERSION)

    def get_client_extensions(self):
        return glXGetClientString(self.display, GLX_EXTENSIONS).split()

    def get_extensions(self):
        return glXQueryExtensionsString(self.display, 0).split()

    def have_extension(self, extension):
        if not self.have_version(1, 1):
            return False
        return extension in self.get_extensions()

# Single instance suitable for apps that use only a single display.
glx_info = None

def set_display(display):
    '''Set the default display used by glx_info.  Called by XlibWindow
    when created on a display.
    '''
    global glx_info 
    glx_info = GLXInfo(display)
