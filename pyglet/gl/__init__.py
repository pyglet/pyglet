#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2007 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

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
