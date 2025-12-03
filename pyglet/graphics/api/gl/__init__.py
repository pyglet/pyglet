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
from pyglet.graphics.api.gl.lib import GLException  # noqa: F401
from .base import ObjectSpace  # noqa: F401
from .context import OpenGLSurfaceContext

_is_pyglet_doc_run = hasattr(_sys, "is_pyglet_doc_run") and _sys.is_pyglet_doc_run
