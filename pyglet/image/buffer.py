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
from pyglet.gl import *


def get_max_color_attachments():
    """Get the maximum allow Framebuffer Color attachements"""
    number = GLint()
    glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS, number)
    return number.value


class Renderbuffer:
    """OpenGL Renderbuffer Object"""

    def __init__(self, width, height, internal_format, samples=1):
        """Create an instance of a Renderbuffer object."""
        self._id = GLuint()
        self._width = width
        self._height = height
        self._internal_format = internal_format

        glGenRenderbuffers(1, self._id)
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)

        if samples > 1:
            glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples, internal_format, width, height)
        else:
            glRenderbufferStorage(GL_RENDERBUFFER, internal_format, width, height)

        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    @property
    def id(self):
        return self._id.value

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

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
        except Exception:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)


class Framebuffer:
    """OpenGL Framebuffer Object"""

    def __init__(self, target=GL_FRAMEBUFFER):
        """Create an OpenGL Framebuffer object.

        :rtype: :py:class:`~pyglet.image.Framebuffer`

        .. versionadded:: 2.0
        """
        self._id = GLuint()
        glGenFramebuffers(1, self._id)
        self._attachment_types = 0
        self._width = 0
        self._height = 0
        self.target = target

    @property
    def id(self):
        return self._id.value

    @property
    def width(self):
        """The width of the widest attachment."""
        return self._width

    @property
    def height(self):
        """The width of the widest attachment."""
        return self._height

    def bind(self):
        glBindFramebuffer(self.target, self._id)

    def unbind(self):
        glBindFramebuffer(self.target, 0)

    def clear(self):
        if self._attachment_types:
            self.bind()
            glClear(self._attachment_types)
            self.unbind()

    def delete(self):
        try:
            glDeleteFramebuffers(1, self._id)
        except Exception:
            pass

    @property
    def is_complete(self):
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

    def attach_texture(self, texture, target=GL_FRAMEBUFFER, attachment=GL_COLOR_ATTACHMENT0):
        """Attach a Texture to the Framebuffer

        :Parameters:
            `texture` : pyglet.image.Texture
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            `target` : int
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            `attachment` : int
                Specifies the attachment point of the framebuffer. attachment must be
                GL_COLOR_ATTACHMENTi, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT or
                GL_DEPTH_STENCIL_ATTACHMENT.
        """
        self.bind()
        glFramebufferTexture(target, attachment, texture.id, texture.level)
        # glFramebufferTexture2D(target, attachment, texture.target, texture.id, texture.level)
        self._attachment_types |= attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_texture_layer(self, texture, layer, level, target=GL_FRAMEBUFFER, attachment=GL_COLOR_ATTACHMENT0):
        """Attach a Texture layer to the Framebuffer

        :Parameters:
            `texture` : pyglet.image.TextureArray
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            `layer` : int
                Specifies the layer of texture to attach.
            `level` : int
                Specifies the mipmap level of texture to attach.
            `target` : int
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            `attachment` : int
                Specifies the attachment point of the framebuffer. attachment must be
                GL_COLOR_ATTACHMENTi, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT or
                GL_DEPTH_STENCIL_ATTACHMENT.
        """
        self.bind()
        glFramebufferTextureLayer(target, attachment, texture.id, level, layer)
        self._attachment_types |= attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_renderbuffer(self, renderbuffer, target=GL_FRAMEBUFFER, attachment=GL_COLOR_ATTACHMENT0):
        """"Attach a Renderbuffer to the Framebuffer

        :Parameters:
            `renderbuffer` : pyglet.image.Renderbuffer
                Specifies the Renderbuffer to attach to the framebuffer attachment
                point named by attachment.
            `target` : int
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            `attachment` : int
                Specifies the attachment point of the framebuffer. attachment must be
                GL_COLOR_ATTACHMENTi, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT or
                GL_DEPTH_STENCIL_ATTACHMENT.
        """
        self.bind()
        glFramebufferRenderbuffer(target, attachment, GL_RENDERBUFFER, renderbuffer.id)
        self._attachment_types |= attachment
        self._width = max(renderbuffer.width, self._width)
        self._height = max(renderbuffer.height, self._height)
        self.unbind()

    def __del__(self):
        try:
            glDeleteFramebuffers(1, self._id)
        # Python interpreter is shutting down:
        except Exception:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)
