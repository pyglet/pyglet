from __future__ import annotations

import pyglet

from pyglet.gl import *

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.image import Texture


def get_max_color_attachments() -> int:
    """Get the maximum allow Framebuffer Color attachements"""
    number = GLint()
    glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS, number)
    return number.value


class Renderbuffer:
    """OpenGL Renderbuffer Object"""

    def __init__(self, width: int, height: int, internal_format: int, samples: int = 1) -> None:
        self._context = pyglet.gl.current_context
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
    def id(self) -> int:
        return self._id.value

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def bind(self) -> None:
        glBindRenderbuffer(GL_RENDERBUFFER, self._id)

    @staticmethod
    def unbind() -> None:
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def delete(self) -> None:
        glDeleteRenderbuffers(1, self._id)
        self._id = None

    def __del__(self):
        if self._id is not None:
            try:
                self._context.delete_renderbuffer(self._id.value)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"


class Framebuffer:
    """OpenGL Framebuffer Object

    .. versionadded:: 2.0
    """
    def __init__(self, target: int = GL_FRAMEBUFFER):
        self._context = pyglet.gl.current_context
        self._id = GLuint()
        glGenFramebuffers(1, self._id)
        self._attachment_types = 0
        self._width = 0
        self._height = 0
        self.target = target

    @property
    def id(self) -> int:
        """The Framebuffer id"""
        return self._id.value

    @property
    def width(self) -> int:
        """The width of the widest attachment."""
        return self._width

    @property
    def height(self) -> int:
        """The height of the tallest attachment."""
        return self._height

    def bind(self) -> None:
        """Bind the Framebuffer

        This ctivates it as the current drawing target.
        """
        glBindFramebuffer(self.target, self._id)

    def unbind(self) -> None:
        """Unbind the Framebuffer

        Unbind should be called to prevent further rendering
        to the framebuffer, or if you wish to access data
        from its Texture atachments.
        """
        glBindFramebuffer(self.target, 0)

    def clear(self) -> None:
        """Clear the attachments"""
        if self._attachment_types:
            self.bind()
            glClear(self._attachment_types)
            self.unbind()

    def delete(self) -> None:
        """Explicitly delete the Framebuffer."""
        glDeleteFramebuffers(1, self._id)
        self._id = None

    def __del__(self):
        if self._id is not None:
            try:
                self._context.delete_framebuffer(self._id.value)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    @property
    def is_complete(self) -> bool:
        """True if the framebuffer is 'complete', else False."""
        return glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    @staticmethod
    def get_status() -> str:
        """Get the current Framebuffer status, as a string.

        If ``Framebuffer.is_complete`` is ``False``, this method
        can be used for more information. It will return a
        string with the OpenGL reported status.
        """
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

    def attach_texture(self, texture: Texture,
                       target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Texture to the Framebuffer

        Args:
            texture:
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            target:
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            attachment:
                Specifies the attachment point of the framebuffer. attachment must be
                GL_COLOR_ATTACHMENTi, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT or
                GL_DEPTH_STENCIL_ATTACHMENT.
        """
        self.bind()
        glFramebufferTexture(target, attachment, texture.id, texture.level)
        self._attachment_types |= attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_texture_layer(self, texture: Texture, layer: int, level: int,
                             target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Texture layer to the Framebuffer

        Args:
            texture:
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            layer:
                Specifies the layer of texture to attach.
            level:
                Specifies the mipmap level of texture to attach.
            target:
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            attachment:
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

    def attach_renderbuffer(self, renderbuffer: Renderbuffer,
                            target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Renderbuffer to the Framebuffer

        Args:
            renderbuffer:
                Specifies the Renderbuffer to attach to the framebuffer attachment
                point named by attachment.
            target:
                Specifies the framebuffer target. target must be GL_DRAW_FRAMEBUFFER,
                GL_READ_FRAMEBUFFER, or GL_FRAMEBUFFER. GL_FRAMEBUFFER is equivalent
                to GL_DRAW_FRAMEBUFFER.
            attachment:
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"
