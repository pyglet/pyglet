#!/usr/bin/env python

'''Information about version and extensions of current GL implementation.

Usage::
    
    from pyglet.gl import gl_info

    if gl_info.have_extension('GL_NV_register_combiners'):
        # ...

If you are using more than one context, you can set up a separate GLInfo
object for each context.  Call `set_active_context` after switching to the
context::

    from pyglet.gl.gl_info import GLInfo

    info = GLInfo()
    info.set_active_context()

    if info.have_version(2, 1):
        # ...

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
import warnings

from pyglet.gl.gl import *

class GLInfo(object):
    have_context = False
    version = '0.0.0'
    vendor = ''
    renderer = ''
    extensions = set()

    def set_active_context(self):
        self.have_context = True
        self.vendor = cast(glGetString(GL_VENDOR), c_char_p).value
        self.renderer = cast(glGetString(GL_RENDERER), c_char_p).value
        self.extensions = cast(glGetString(GL_EXTENSIONS), c_char_p).value
        if self.extensions:
            self.extensions = set(self.extensions.split())
        self.version = cast(glGetString(GL_VERSION), c_char_p).value

    def have_extension(self, extension):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return extension in self.extensions

    def get_extensions(self):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.extensions

    def get_version(self):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.version

    def have_version(self, major, minor=0, release=0):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        ver = '%s.0.0' % self.version.split(' ', 1)[0]
        imajor, iminor, irelease = [int(v) for v in ver.split('.', 3)[:3]]
        return imajor > major or \
           (imajor == major and iminor > minor) or \
           (imajor == major and iminor == minor and irelease >= release)

    def get_renderer(self):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.renderer

    def get_vendor(self):
        if not self.have_context:
            warnings.warn('No GL context created yet.')
        return self.vendor

# Single instance useful for apps with only a single context (or all contexts
# have same GL driver, common case). 
_gl_info = GLInfo()

set_active_context = _gl_info.set_active_context
have_extension = _gl_info.have_extension
get_extensions = _gl_info.get_extensions
get_version = _gl_info.get_version
have_version = _gl_info.have_version
get_renderer = _gl_info.get_renderer
get_vendor = _gl_info.get_vendor
