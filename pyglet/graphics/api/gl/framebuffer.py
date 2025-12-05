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

from pyglet.customtypes import DataTypes
from pyglet.enums import FramebufferTarget, FramebufferAttachment, ComponentFormat
from pyglet.graphics.api.gl import gl, GL_RGBA, GL_UNSIGNED_BYTE, GLuint
from pyglet.image.base import ImageData
from pyglet.graphics.api.gl.texture import _get_internal_format

if TYPE_CHECKING:
    from pyglet.graphics.api.gl import OpenGLSurfaceContext
    from pyglet.graphics.api.gl.texture import Texture

_gl_target_map = {
    FramebufferTarget.FRAMEBUFFER: gl.GL_FRAMEBUFFER,
    FramebufferTarget.DRAW:       gl.GL_DRAW_FRAMEBUFFER,
    FramebufferTarget.READ:       gl.GL_READ_FRAMEBUFFER,
}

_gl_attachment_map = {
    FramebufferAttachment.COLOR0:        gl.GL_COLOR_ATTACHMENT0,
    FramebufferAttachment.COLOR1:        gl.GL_COLOR_ATTACHMENT1,
    FramebufferAttachment.COLOR2:        gl.GL_COLOR_ATTACHMENT2,
    FramebufferAttachment.COLOR3:        gl.GL_COLOR_ATTACHMENT3,
    FramebufferAttachment.COLOR4:        gl.GL_COLOR_ATTACHMENT4,
    FramebufferAttachment.COLOR5:        gl.GL_COLOR_ATTACHMENT5,
    FramebufferAttachment.COLOR6:        gl.GL_COLOR_ATTACHMENT6,
    FramebufferAttachment.COLOR7:        gl.GL_COLOR_ATTACHMENT7,
    FramebufferAttachment.COLOR8:        gl.GL_COLOR_ATTACHMENT8,
    FramebufferAttachment.COLOR9:        gl.GL_COLOR_ATTACHMENT9,
    FramebufferAttachment.COLOR10:       gl.GL_COLOR_ATTACHMENT10,
    FramebufferAttachment.COLOR11:       gl.GL_COLOR_ATTACHMENT11,
    FramebufferAttachment.COLOR12:       gl.GL_COLOR_ATTACHMENT12,
    FramebufferAttachment.COLOR13:       gl.GL_COLOR_ATTACHMENT13,
    FramebufferAttachment.COLOR14:       gl.GL_COLOR_ATTACHMENT14,
    FramebufferAttachment.COLOR15:       gl.GL_COLOR_ATTACHMENT15,

    FramebufferAttachment.DEPTH:         gl.GL_DEPTH_ATTACHMENT,
    FramebufferAttachment.STENCIL:       gl.GL_STENCIL_ATTACHMENT,
    FramebufferAttachment.DEPTH_STENCIL: gl.GL_DEPTH_STENCIL_ATTACHMENT,
}


def get_viewport() -> tuple:
    """Get the current OpenGL viewport dimensions (left, bottom, right, top)."""
    ctx = pyglet.graphics.api.core.current_context
    viewport = (gl.GLint * 4)()
    ctx.glGetIntegerv(gl.GL_VIEWPORT, viewport)
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

    buf = (gl.GLubyte * (len(fmt) * width * height))()

    ctx.glReadBuffer(gl.GL_BACK)
    ctx.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
    ctx.glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, buf)
    return ImageData(width, height, fmt, buf)




def get_max_color_attachments() -> int:
    """Return the maximum number of color attachments supported by the current context."""
    return pyglet.graphics.api.core.current_context.get_info().MAX_COLOR_ATTACHMENTS


class Renderbuffer:
    """OpenGL Renderbuffer Object."""

    def __init__(self, context: OpenGLSurfaceContext, width: int, height: int,
                 component_format: ComponentFormat, bit_size: int, data_type: DataTypes = "I", samples: int = 1) -> None:
        """Create a RenderBuffer instance."""
        self._context = context or pyglet.graphics.api.core.current_context
        self._id = GLuint()
        self._width = width
        self._height = height
        self._internal_format = _get_internal_format(component_format, bit_size, data_type)

        self._context.glGenRenderbuffers(1, self._id)
        self._context.glBindRenderbuffer(gl.GL_RENDERBUFFER, self._id)

        if samples > 1:
            self._context.glRenderbufferStorageMultisample(gl.GL_RENDERBUFFER, samples, self._internal_format, width, height)
        else:
            self._context.glRenderbufferStorage(gl.GL_RENDERBUFFER, self._internal_format, width, height)

        self._context.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)

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
        self._context.glBindRenderbuffer(gl.GL_RENDERBUFFER, self._id)

    def unbind(self) -> None:
        self._context.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)

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


_status_states = {
    gl.GL_FRAMEBUFFER_UNSUPPORTED: "Framebuffer unsupported. Try another format.",
    gl.GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT: "Framebuffer incomplete attachment.",
    gl.GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT: "Framebuffer missing attachment.",
    gl.GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT: "Framebuffer unsupported dimension.",
    gl.GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT: "Framebuffer incomplete formats.",
    gl.GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER: "Framebuffer incomplete draw buffer.",
    gl.GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER: "Framebuffer incomplete read buffer.",
    gl.GL_FRAMEBUFFER_COMPLETE: "Framebuffer is complete.",
}

class Framebuffer:
    """OpenGL Framebuffer Object.

    .. versionadded:: 2.0
    """
    def __init__(self, target: FramebufferTarget = FramebufferTarget.FRAMEBUFFER, context: OpenGLSurfaceContext | None = None) -> None:
        self._context = context or pyglet.graphics.api.core.current_context
        self._id = GLuint()
        self._context.glGenFramebuffers(1, self._id)
        self._attachment_types = 0
        self._width = 0
        self._height = 0
        self.target = target
        self._gl_target = _gl_target_map[target]

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

        This activates it as the current drawing target.
        """
        self._context.glBindFramebuffer(self._gl_target, self._id)

    def unbind(self) -> None:
        """Unbind the Framebuffer.

        Unbind should be called to prevent further rendering
        to the framebuffer, or if you wish to access data
        from its Texture atachments.
        """
        self._context.glBindFramebuffer(self._gl_target, 0)

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
        return self._context.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) == gl.GL_FRAMEBUFFER_COMPLETE

    def get_status(self) -> str:
        """Get the current Framebuffer status, as a string.

        If ``Framebuffer.is_complete`` is ``False``, this method
        can be used for more information. It will return a
        string with the OpenGL reported status.
        """
        gl_status = self._context.glCheckFramebufferStatus(self._gl_target)

        return _status_states.get(gl_status, "Unknown error")

    def attach_texture(self, texture: Texture, attachment: FramebufferAttachment = FramebufferAttachment.COLOR0) -> None:
        """Attach a Texture to the Framebuffer.

        Args:
            texture:
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            attachment:
                Specifies the attachment point of the framebuffer.
        """
        self.bind()
        gl_attachment = _gl_attachment_map[attachment]
        self._context.glFramebufferTexture(self._gl_target, gl_attachment, texture.id, texture.level)
        self._attachment_types |= gl_attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_texture_layer(self, texture: Texture, layer: int, level: int,
                             attachment: FramebufferAttachment = FramebufferAttachment.COLOR0) -> None:
        """Attach a Texture layer to the Framebuffer.

        Args:
            texture:
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            layer:
                Specifies the layer of texture to attach.
            level:
                Specifies the mipmap level of texture to attach.
            attachment:
                Specifies the attachment point of the framebuffer.
        """
        self.bind()
        gl_attachment = _gl_attachment_map[attachment]
        self._context.glFramebufferTextureLayer(self._gl_target, gl_attachment, texture.id, level, layer)
        self._attachment_types |= gl_attachment
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_renderbuffer(self, renderbuffer: Renderbuffer,
                            attachment: FramebufferAttachment = FramebufferAttachment.COLOR0) -> None:
        """Attach a Renderbuffer to the Framebuffer.

        Args:
            renderbuffer:
                Specifies the Renderbuffer to attach to the framebuffer attachment
                point named by attachment.
            attachment:
                Specifies the attachment point of the framebuffer.
        """
        self.bind()
        gl_attachment = _gl_attachment_map[attachment]
        self._context.glFramebufferRenderbuffer(self._gl_target, gl_attachment, gl.GL_RENDERBUFFER, renderbuffer.id)
        self._attachment_types |= gl_attachment
        self._width = max(renderbuffer.width, self._width)
        self._height = max(renderbuffer.height, self._height)
        self.unbind()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"
