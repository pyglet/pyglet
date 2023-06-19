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

``pyglet.gl.gl``
    OpenGL
``pyglet.gl.gl.glext_arb``
    ARB registered OpenGL extension functions

These subpackages are also available, but are not imported into this namespace
by default:

``pyglet.gl.glext_nv``
    nVidia OpenGL extension functions
``pyglet.gl.agl``
    AGL (Mac OS X OpenGL context functions)
``pyglet.gl.glx``
    GLX (Linux OpenGL context functions)
``pyglet.gl.glxext_arb``
    ARB registered GLX extension functions
``pyglet.gl.glxext_nv``
    nvidia GLX extension functions
``pyglet.gl.wgl``
    WGL (Windows OpenGL context functions)
``pyglet.gl.wglext_arb``
    ARB registered WGL extension functions
``pyglet.gl.wglext_nv``
    nvidia WGL extension functions

The information modules are provided for convenience, and are documented below.
"""
import pyglet as _pyglet

from pyglet.gl.gl import *
from pyglet.gl.lib import GLException
from pyglet.gl import gl_info
from pyglet.gl.gl_compat import GL_LUMINANCE, GL_INTENSITY

from pyglet import compat_platform
from .base import ObjectSpace, CanvasConfig, Context

import sys as _sys
_is_pyglet_doc_run = hasattr(_sys, "is_pyglet_doc_run") and _sys.is_pyglet_doc_run

#: The active OpenGL context.
#:
#: You can change the current context by calling `Context.set_current`;
#: do not modify this global.
#:
#: :type: `Context`
#:
#: .. versionadded:: 1.1
current_context = None


class ContextException(Exception):
    pass


class ConfigException(Exception):
    pass


if _pyglet.options['debug_texture']:
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


def _create_shadow_window():
    global _shadow_window

    import pyglet
    if not pyglet.options['shadow_window'] or _is_pyglet_doc_run:
        return

    from pyglet.window import Window

    class ShadowWindow(Window):
        def __init__(self):
            super().__init__(width=1, height=1, visible=False)

        def _create_projection(self):
            """Shadow window does not need a projection."""
            pass

    _shadow_window = ShadowWindow()
    _shadow_window.switch_to()

    from pyglet import app
    app.windows.remove(_shadow_window)


if _is_pyglet_doc_run:
    from .base import Config

elif _pyglet.options['headless']:
    from .headless import HeadlessConfig as Config
elif compat_platform in ('win32', 'cygwin'):
    from .win32 import Win32Config as Config
elif compat_platform.startswith('linux'):
    from .xlib import XlibConfig as Config
elif compat_platform == 'darwin':
    from .cocoa import CocoaConfig as Config


_shadow_window = None

# Import pyglet.window now if it isn't currently being imported (this creates the shadow window).
if not _is_pyglet_doc_run and 'pyglet.window' not in _sys.modules and _pyglet.options['shadow_window']:
    # trickery is for circular import
    _pyglet.gl = _sys.modules[__name__]
    import pyglet.window
