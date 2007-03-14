#!/usr/bin/env python

'''Information about version and extensions of current GLX implementation.

Usage::

    from pyglet.gl import glx_info

    if glx_info.have_extension('GLX_NV_float_buffer'):
        # ...

Or, if using more than one display::

    from pyglet.gl.glx_info import GLXInfo

    info = GLXInfo(window._display)
    if info.get_server_vendor() == 'ATI':
        # ...

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.gl.glx import *
from pyglet.gl.glx import Display

class GLXInfoException(Exception):
    pass

class GLXInfo(object):
    def __init__(self, display=None):
        self.display = display

    def set_display(self, display):
        self.display = cast(pointer(display), POINTER(Display))

    def check_display(self):
        if not self.display:
            raise GLXInfoException('No X11 display has been set yet.')

    def have_version(self, major, minor=0):
        self.check_display()
        if not glXQueryExtension(self.display, None, None):
            raise GLXInfoException('pyglet requires an X server with GLX')

        server = [int(i) for i in self.get_server_version().split('.')]
        client = [int(i) for i in self.get_client_version().split('.')]
        return (tuple(server) >= (major, minor) and 
                tuple(client) >= (major, minor))

    def get_server_vendor(self):
        self.check_display()
        return glXQueryServerString(self.display, 0, GLX_VENDOR)
    
    def get_server_version(self):
        # glXQueryServerString was introduced in GLX 1.1, so we need to use the
        # 1.0 function here which queries the server implementation for its
        # version.
        self.check_display()
        major = c_int()
        minor = c_int()
        if not glXQueryVersion(self.display, byref(major), byref(minor)):
            raise GLXInfoException('Could not determine GLX server version')
        return '%s.%s'%(major.value, minor.value)

    def get_server_extensions(self):
        self.check_display()
        return glXQueryServerString(self.display, 0, GLX_EXTENSIONS).split()

    def get_client_vendor(self):
        self.check_display()
        return glXGetClientString(self.display, GLX_VENDOR)

    def get_client_version(self):
        self.check_display()
        return glXGetClientString(self.display, GLX_VERSION)

    def get_client_extensions(self):
        self.check_display()
        return glXGetClientString(self.display, GLX_EXTENSIONS).split()

    def get_extensions(self):
        self.check_display()
        return glXQueryExtensionsString(self.display, 0).split()

    def have_extension(self, extension):
        self.check_display()
        if not self.have_version(1, 1):
            return False
        return extension in self.get_extensions()

# Single instance suitable for apps that use only a single display.
_glx_info = None

set_display = _glx_info.set_display
check_display = _glx_info.check_display
have_version = _glx_info.have_version
get_server_vendor = _glx_info.get_server_vendor
get_server_version = _glx_info.get_server_version
get_server_extensions = _glx_info.get_server_extensions
get_client_vendor = _glx_info.get_client_vendor
get_client_version = _glx_info.get_client_version
get_client_extensions = _glx_info.get_client_extensions
get_extensions = _glx_info.get_extensions
have_extension = _glx_info.have_extension
