#!/usr/bin/env python

'''OpenGL and GLU interface.

This package imports all OpenGL, GLU and registered OpenGL extension
functions.  Functions have identical signatures to their C counterparts.  For
example::

    from pyglet.gl import *
    
    # [...omitted: set up a GL context and framebuffer]
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(0.1, 0.2, 0.3)
    glVertex3f(0.1, 0.2, 0.3)
    glEnd()

OpenGL is documented in full at the `OpenGL Reference Pages`_.  

The `OpenGL Programming Guide`_ is a popular reference manual organised by
topic.  The free online version documents only OpenGL 1.1.  `Later editions`_
cover more recent versions of the API and can be purchased from a book store.

.. _OpenGL Reference Pages: http://www.opengl.org/documentation/red_book/
.. _OpenGL Programming Guide: http://fly.cc.fer.hr/~unreal/theredbook/
.. _Later editions: http://www.opengl.org/documentation/red_book/

The following subpackages are imported into this "mega" package already (and
so are available by importing ``pyglet.gl``):

``pyglet.gl.gl``
    OpenGL
``pyglet.gl.glu``
    GLU
``pyglet.gl.gl.glext_abi``
    ARB registered OpenGL extension functions
``pyglet.gl.gl.glext_missing``
    ARB registered OpenGL extension functions not included in the ARB C header

These subpackages are also available, but are not imported into this namespace
by default:

``pyglet.gl.glext_nv``
    nVidia OpenGL extension functions
``pyglet.gl.agl``
    AGL (Mac OS X OpenGL context functions)
``pyglet.gl.glx``
    GLX (Linux OpenGL context functions)
``pyglet.gl.glxext_abi``
    ARB registered GLX extension functions
``pyglet.gl.glxext_nv``
    nvidia GLX extension functions
``pyglet.gl.wgl``
    WGL (Windows OpenGL context functions)
``pyglet.gl.wglext_abi``
    ARB registered WGL extension functions
``pyglet.gl.wglext_nv``
    nvidia WGL extension functions

The information modules are provided for convenience, and are documented
below.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.gl.lib import GLException
from pyglet.gl.gl import *
from pyglet.gl.glu import *
from pyglet.gl.glext_abi import *
from pyglet.gl.glext_missing import *
