"""OpenGL interface.

This package imports all OpenGL and registered OpenGL extension
functions.  Functions have identical signatures to their C counterparts.

OpenGL is documented in full at the `OpenGL Reference Pages`_.

The `OpenGL Programming Guide`_, also known as "The Red Book", is a popular
reference manual organised by topic. It is available in digital and paper
editions.

.. _OpenGL Reference Pages: https://www.khronos.org/registry/OpenGL-Refpages/
.. _OpenGL Programming Guide: http://opengl-redbook.com/

The following subpackages are imported into this "mega" package already
(and so are available by importing ``pyglet.gl``):

``pyglet.graphics.api.gl.gl``
    OpenGL
``pyglet.graphics.api.gl.gl.glext_arb``
    ARB registered OpenGL extension functions
``pyglet.graphics.api.gl.gl.gl_compat``
    Deprecated OpenGL extension functions.

These subpackages are also available, but are not imported into this namespace
by default:

``pyglet.graphics.api.gl.glext_nv``
    nVidia OpenGL extension functions
``pyglet.graphics.api.gl.agl``
    AGL (Mac OS X OpenGL context functions)
``pyglet.graphics.api.gl.glx``
    GLX (Linux OpenGL context functions)
``pyglet.graphics.api.gl.glxext_arb``
    ARB registered GLX extension functions
``pyglet.graphics.api.gl.glxext_nv``
    nvidia GLX extension functions
``pyglet.graphics.api.gl.wgl``
    WGL (Windows OpenGL context functions)
``pyglet.graphics.api.gl.wglext_arb``
    ARB registered WGL extension functions
``pyglet.graphics.api.gl.wglext_nv``
    nvidia WGL extension functions

The information modules are provided for convenience, and are documented below.
"""
from __future__ import annotations

import sys as _sys

import pyglet as _pyglet
from pyglet import compat_platform
from pyglet.graphics.api.gl.gl import *  # Must always be imported before gl_info or bad things happen.  # noqa: F403
from pyglet.graphics.api.gl1.gl_compat import GL_INTENSITY, GL_LUMINANCE
from pyglet.graphics.api.gl.lib import GLException  # noqa: F401
from .base import OpenGLWindowConfig, OpenGLSurfaceContext, ObjectSpace  # noqa: F401

_is_pyglet_doc_run = hasattr(_sys, "is_pyglet_doc_run") and _sys.is_pyglet_doc_run

if _pyglet.options.debug_texture:
    _debug_texture_total = 0
    _debug_texture_sizes = {}
    _debug_texture = None


    def _debug_texture_alloc(texture, size):
        global _debug_texture_total

        _debug_texture_sizes[texture] = size
        _debug_texture_total += size

        print(f'{_debug_texture_total} (+{size})')


    def _debug_texture_dealloc(texture):
        global _debug_texture_total

        size = _debug_texture_sizes[texture]
        del _debug_texture_sizes[texture]
        _debug_texture_total -= size

        print(f'{_debug_texture_total} (-{size})')


    _glBindTexture = glBindTexture


    def glBindTexture(target, texture):
        global _debug_texture
        _debug_texture = texture
        return _glBindTexture(target, texture)


    _glTexImage2D = glTexImage2D


    def glTexImage2D(target, level, internalformat, width, height, border,
                     format, type, pixels):
        try:
            _debug_texture_dealloc(_debug_texture)
        except KeyError:
            pass

        if internalformat in (1, GL_ALPHA, GL_INTENSITY, GL_LUMINANCE):
            depth = 1
        elif internalformat in (2, GL_RGB16, GL_RGBA16):
            depth = 2
        elif internalformat in (3, GL_RGB):
            depth = 3
        else:
            depth = 4  # Pretty crap assumption
        size = (width + 2 * border) * (height + 2 * border) * depth
        _debug_texture_alloc(_debug_texture, size)

        return _glTexImage2D(target, level, internalformat, width, height, border, format, type, pixels)


    _glDeleteTextures = glDeleteTextures


    def glDeleteTextures(n, textures):
        if not hasattr(textures, '__len__'):
            _debug_texture_dealloc(textures.value)
        else:
            for i in range(n):
                _debug_texture_dealloc(textures[i].value)

        return _glDeleteTextures(n, textures)

if _is_pyglet_doc_run:
    from .base import OpenGLConfig

elif _pyglet.options.headless:
    from .egl.context import HeadlessContext as OpenGLConfig
elif compat_platform in ('win32', 'cygwin'):
    from .win32.context import Win32OpenGLConfig as OpenGLConfig
elif compat_platform.startswith('linux'):
    from .xlib.context import XlibOpenGLConfig as OpenGLConfig
elif compat_platform == 'darwin':
    from .cocoa.context import CocoaOpenGLConfig as OpenGLConfig
else:
    msg = f"Platform not currently supported: {compat_platform}"
    raise Exception(msg)
