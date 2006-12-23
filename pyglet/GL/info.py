#!/usr/bin/env python

'''Cached information about version and extensions of current GL
implementation.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import warnings

# We have to wait until a context is created (with a window) until any
# information is available.
_have_context = False

# The information that gets filled in
_version = '0.0.0'
_vendor = ''
_renderer = ''
_extensions = []

# Called by GLContext when created and made current.
def set_context():
    from pyglet.GL.VERSION_1_1 import (glGetString, glGetError,
        GL_VENDOR, GL_RENDERER, GL_EXTENSIONS, GL_VERSION,
        GL_INVALID_ENUM, GL_INVALID_OPERATION)

    global _have_context, _vendor, _renderer, _extensions, _version
    if _have_context:
        return

    _have_context = True
    _vendor = glGetString(GL_VENDOR)
    _renderer = glGetString(GL_RENDERER)
    _extensions = glGetString(GL_EXTENSIONS)
    if _extensions:
        _extensions = _extensions.split()
    else:
        error = glGetError()
        if error == GL_INVALID_ENUM:
            _extensions = ['[unknown - GL_EXTENSIONS not supported]']
        elif error == GL_INVALID_OPERATION:
            raise ValueError('glGetString incorrectly called between '
                'glBegin and glEnd')
        _extensions = []
    _version = glGetString(GL_VERSION)

def have_context():
    return _have_context

def have_extension(extension):
    if not _have_context:
        warnings.warn('No GL context created yet.')
    return extension in _extensions

def get_extensions():
    if not _have_context:
        warnings.warn('No GL context created yet.')
    return _extensions

def get_version():
    if not _have_context:
        warnings.warn('No GL context created yet.')
    return _version

def have_version(major, minor=0, release=0):
    if not _have_context:
        warnings.warn('No GL context created yet.')
    ver = '%s.0.0' % _version.split(' ', 1)[0]
    imajor, iminor, irelease = [int(v) for v in ver.split('.', 3)[:3]]
    return imajor > major or \
       (imajor == major and iminor > minor) or \
       (imajor == major and iminor == minor and irelease >= release)

def get_renderer():
    if not _have_context:
        warnings.warn('No GL context created yet.')
    return _renderer

def get_vendor():
    if not _have_context:
        warnings.warn('No GL context created yet.')
    return _vendor
