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
import weakref

from pyglet.gl import *
from pyglet.image import Texture

__all__ = ['Framebuffer']


def _get_max_color_attachments():
    number = GLint()
    glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS, number)
    return number.value


class Renderbuffer:
    """OpenGL Renderbuffer Object"""

    def __init__(self, width, height, internal_format=GL_RGB8):
        """Create an instance of a Renderbuffer object."""
        self._id = GLuint()
        glGenRenderbuffers(1, self._id)
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)
        glRenderbufferStorage(GL_RENDERBUFFER, internal_format, width, height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    @property
    def id(self):
        return self._id.value

    def bind(self):
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)

    @staticmethod
    def unbind():
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def delete(self):
        glDeleteRenderbuffers(1, self._id)

    def __del__(self):
        try:
            glDeleteRenderbuffers(1, self._id)
        # Python interpreter is shutting down:
        except ImportError:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)


class RenderbufferMultisample:

    def __init__(self, width, height, internal_format, samples):
        self._id = GLuint()
        glGenRenderbuffers(1, self._id)
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples, internal_format, width, height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    @property
    def id(self):
        return self._id.value

    def bind(self):
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)

    @staticmethod
    def unbind():
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def delete(self):
        glDeleteRenderbuffers(1, self._id)

    def __del__(self):
        try:
            glDeleteRenderbuffers(1, self._id)
        # Python interpreter is shutting down:
        except ImportError:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)


class Framebuffer:
    """OpenGL Framebuffer Object"""

    _max_color_attachments = _get_max_color_attachments()

    def __init__(self):
        """Create an instance of a Framebuffer object."""
        self._id = GLuint()
        glGenFramebuffers(1, self._id)

        self._color_attachments = weakref.WeakSet()
        self._depth_attachments = None
        self._stencil_attachments = None
        self._depth_stencil_attachments = None

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

    def attach_color(self, image):
        number = GL_COLOR_ATTACHMENT0 + len(self._color_attachments)
        assert number <= self._max_color_attachments, "Exceeded maximum supported color attachments"
        glFramebufferTexture2D(GL_FRAMEBUFFER, number, GL_TEXTURE_2D, image, 0)
        self._color_attachments.add(image)

    def attach_depth(self, image):
        pass

    def attach_stencil(self, image):
        pass

    def attach_depth_stencil(self, image):
        pass

    def __del__(self):
        try:
            glDeleteFramebuffers(1, self._id)
        # Python interpreter is shutting down:
        except ImportError:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)
