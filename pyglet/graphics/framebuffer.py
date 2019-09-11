# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2019 pyglet contributors
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

from pyglet.gl import GLuint, glBindFramebuffer, glCheckFramebufferStatus, glDeleteFramebuffers, glGenFramebuffers
from pyglet.gl import GL_FRAMEBUFFER, GL_FRAMEBUFFER_COMPLETE, GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT
from pyglet.gl import GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT, GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER
from pyglet.gl import GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT, GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT
from pyglet.gl import GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER, GL_FRAMEBUFFER_UNSUPPORTED

__all__ = ['Framebuffer']


class Framebuffer:
    """OpenGL Framebuffer Object"""

    def __init__(self):
        """Create an instance of a Framebuffer object."""
        self._id = GLuint()
        glGenFramebuffers(1, self._id)

    @property
    def id(self):
        return self._id.value

    def bind(self, target=GL_FRAMEBUFFER):
        glBindFramebuffer(target, self._id)

    @staticmethod
    def unbind(target=GL_FRAMEBUFFER):
        glBindFramebuffer(target, 0)

    def delete(self):
        glDeleteFramebuffers(1, self._id)

    @property
    def is_compete(self):
        return glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    @staticmethod
    def get_status():
        states = {GL_FRAMEBUFFER_UNSUPPORTED: "Framebuffer unsupported. Try another format.",
                  GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT: "Framebuffer incomplete attachment.",
                  GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT: "Framebuffer missing attachment.",
                  GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT: "Framebuffer unsupported dimension.",
                  GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT: "Framebuffer incomplete formats.",
                  GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER: "Framebuffer incomplete draw buffer.",
                  GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER: "Framebuffer incomplete read buffer.",
                  GL_FRAMEBUFFER_COMPLETE: "Framebuffer is complete."}

        gl_status = glCheckFramebufferStatus(GL_FRAMEBUFFER)

        return states.get(gl_status, "Unknown error")

    def __del__(self):
        try:
            glDeleteFramebuffers(1, self._id)
        # Python interpreter is shutting down:
        except ImportError:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)
