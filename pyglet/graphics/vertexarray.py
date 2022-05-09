# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
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
#  * Neither the name of pyglet nor the names of its
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

import pyglet

from pyglet.gl import GLuint, glGenVertexArrays, glDeleteVertexArrays, glBindVertexArray


__all__ = ['VertexArray']


class VertexArray:
    """OpenGL Vertex Array Object"""

    def __init__(self):
        """Create an instance of a Vertex Array object."""
        self._context = pyglet.gl.current_context
        self._id = GLuint()
        glGenVertexArrays(1, self._id)

    @property
    def id(self):
        return self._id.value

    def bind(self):
        glBindVertexArray(self._id)

    @staticmethod
    def unbind():
        glBindVertexArray(0)

    def delete(self):
        try:
            glDeleteVertexArrays(1, self._id)
        except Exception:
            pass

    __enter__ = bind

    def __exit__(self, *_):
        glBindVertexArray(0)

    def __del__(self):
        try:
            self._context.delete_vao(self.id)
        # Python interpreter is shutting down:
        except ImportError:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)
