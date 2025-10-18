"""OpenGL Framebuffer abstractions.

This module provides classes for working with Framebuffers & Renderbuffers
and their attachments. Attachments can be pyglet Texture objects, which allows
easily accessing their data, saving to disk, etc. Renderbuffers can be used
if you don't need to access their data at a later time. For example::

    # Create two objects to use as attachments for our Framebuffer.
    color_buffer = pyglet.graphics.Texture.create(width, height, min_filter=GL_NEAREST, mag_filter=GL_NEAREST)
    depth_buffer = pyglet.image.buffer.Renderbuffer(width, height, GL_DEPTH_COMPONENT)

    # Create a framebuffer object, and attach the two buffers:
    framebuffer = pyglet.image.Framebuffer()
    framebuffer.attach_texture(color_buffer, attachment=GL_COLOR_ATTACHMENT0)
    framebuffer.attach_renderbuffer(depth_buffer, attachment=GL_DEPTH_ATTACHMENT)

    # Bind the Framebuffer, which sets it as the active render target:
    framebuffer.bind()

See the OpenGL documentation for more information on valid attachment types and targets.
"""
from __future__ import annotations


import pyglet
from typing import TYPE_CHECKING
from pyglet.graphics.api.gl.gl import GLint, GL_VIEWPORT, GL_BACK, GLubyte, \
    GL_PACK_ALIGNMENT, GL_UNSIGNED_BYTE, GL_RGBA, GLuint, \
    GL_RENDERBUFFER, \
    GL_FRAMEBUFFER, \
    GL_FRAMEBUFFER_COMPLETE, GL_FRAMEBUFFER_UNSUPPORTED, GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT, \
    GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT, GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT, \
    GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT, GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER, GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER, \
    GL_COLOR_ATTACHMENT0
from pyglet.image.base import ImageData

if TYPE_CHECKING:
    from pyglet.graphics.api.gl import OpenGLSurfaceContext
    from pyglet.graphics.api.gl.texture import Texture



def get_viewport() -> tuple:
    """Get the current OpenGL viewport dimensions (left, bottom, right, top)."""
    ctx = pyglet.graphics.api.core.current_context
    viewport = (GLint * 4)()
    ctx.glGetIntegerv(GL_VIEWPORT, viewport)
    return tuple(viewport)

def get_screenshot() -> ImageData:
    """Read the pixel data from the default color buffer into ImageData.

    This provides a simplistic screenshot of the default frame buffer.

    This may be inaccurate if you utilize multiple frame buffers in your program.

    .. versionadded:: 3.0
    """
    ctx = pyglet.graphics.api.core.current_context
    fmt = 'RGBA'
    viewport = get_viewport()
    width = viewport[2]
    height = viewport[3]

    buf = (GLubyte * (len(fmt) * width * height))()

    ctx.glReadBuffer(GL_BACK)
    ctx.glPixelStorei(GL_PACK_ALIGNMENT, 1)
    ctx.glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, buf)
    return ImageData(width, height, fmt, buf)




def get_max_color_attachments() -> int:
    """Return the maximum number of color attachments supported by the current context."""
    return pyglet.graphics.api.core.current_context.get_info().MAX_COLOR_ATTACHMENTS


class Renderbuffer:
    """OpenGL Renderbuffer Object."""

    def __init__(self, context: OpenGLSurfaceContext, width: int, height: int, internal_format: int, samples: int = 1) -> None:
        """Create a RenderBuffer instance."""
        self._context = context or pyglet.graphics.api.core.current_context
        self._id = GLuint()
        self._width = width
        self._height = height
        self._internal_format = internal_format

        self._context.glGenRenderbuffers(1, self._id)
        self._context.glBindRenderbuffer(GL_RENDERBUFFER, self._id)

        if samples > 1:
            self._context.glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples, internal_format, width, height)
        else:
            self._context.glRenderbufferStorage(GL_RENDERBUFFER, internal_format, width, height)

        self._context.glBindRenderbuffer(GL_RENDERBUFFER, 0)

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
        self._context.glBindRenderbuffer(GL_RENDERBUFFER, self._id)

    def unbind(self) -> None:
        self._context.glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def delete(self) -> None:
        self._context.glDeleteRenderbuffers(1, self._id)
        self._id = None

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_renderbuffer(self._id.value)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"


class Framebuffer:
    """OpenGL Framebuffer Object.

    .. versionadded:: 2.0
    """
    def __init__(self, context: OpenGLSurfaceContext, target: int = GL_FRAMEBUFFER) -> None:
        self._context = context or pyglet.graphics.api.core.current_context
        self._id = GLuint()
        self._context.glGenFramebuffers(1, self._id)
        self._attachment_types = 0
        self._width = 0
        self._height = 0
        self.target = target

    @property
    def id(self) -> int:
        """The Framebuffer id."""
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
        """Bind the Framebuffer.

        This ctivates it as the current drawing target.
        """
        self._context.glBindFramebuffer(self.target, self._id)

    def unbind(self) -> None:
        """Unbind the Framebuffer.

        Unbind should be called to prevent further rendering
        to the framebuffer, or if you wish to access data
        from its Texture atachments.
        """
        self._context.glBindFramebuffer(self.target, 0)

    def clear(self) -> None:
        """Clear the attachments."""
        if self._attachment_types:
            self.bind()
            self._context.glClear(self._attachment_types)
            self.unbind()

    def delete(self) -> None:
        """Explicitly delete the Framebuffer."""
        self._context.glDeleteFramebuffers(1, self._id)
        self._id = None

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_framebuffer(self._id.value)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    @property
    def is_complete(self) -> bool:
        """True if the framebuffer is 'complete', else False."""
        return self._context.glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    def get_status(self) -> str:
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

        gl_status = self._context.glCheckFramebufferStatus(GL_FRAMEBUFFER)

        return states.get(gl_status, "Unknown error")

    def attach_texture(self, texture: Texture,
                       target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Texture to the Framebuffer.

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
        self._context.glFramebufferTexture(target, attachment, texture.id, texture.level)
        self._attachment_types |= attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_texture_layer(self, texture: Texture, layer: int, level: int,
                             target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Texture layer to the Framebuffer.

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
        self._context.glFramebufferTextureLayer(target, attachment, texture.id, level, layer)
        self._attachment_types |= attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_renderbuffer(self, renderbuffer: Renderbuffer,
                            target: int = GL_FRAMEBUFFER, attachment: int = GL_COLOR_ATTACHMENT0) -> None:
        """Attach a Renderbuffer to the Framebuffer.

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
        self._context.glFramebufferRenderbuffer(target, attachment, GL_RENDERBUFFER, renderbuffer.id)
        self._attachment_types |= attachment
        self._width = max(renderbuffer.width, self._width)
        self._height = max(renderbuffer.height, self._height)
        self.unbind()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"
