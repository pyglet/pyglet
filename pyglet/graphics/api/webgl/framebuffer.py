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
import js  # noqa: F821
from typing import TYPE_CHECKING

from pyglet.enums import FramebufferTarget, FramebufferAttachment, ComponentFormat
from pyglet.graphics.api.webgl import gl
from pyglet.graphics.api.webgl.texture import _get_internal_format
from pyglet.graphics.resource import FramebufferResource, RenderbufferResource
from pyglet.image.base import ImageData

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl.webgl_js import WebGLFramebuffer as WebGLFramebufferObject, WebGLRenderbuffer as WebGLRenderbufferObject
    from pyglet.customtypes import DataTypes
    from pyglet.graphics.api.webgl import OpenGLSurfaceContext
    from pyglet.graphics.api.webgl.texture import WebGLTexture

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

_clear_bit_map = {
    **dict.fromkeys((
        FramebufferAttachment.COLOR0, FramebufferAttachment.COLOR1,
        FramebufferAttachment.COLOR2, FramebufferAttachment.COLOR3,
        FramebufferAttachment.COLOR4, FramebufferAttachment.COLOR5,
        FramebufferAttachment.COLOR6, FramebufferAttachment.COLOR7,
        FramebufferAttachment.COLOR8, FramebufferAttachment.COLOR9,
        FramebufferAttachment.COLOR10, FramebufferAttachment.COLOR11,
        FramebufferAttachment.COLOR12, FramebufferAttachment.COLOR13,
        FramebufferAttachment.COLOR14, FramebufferAttachment.COLOR15,
    ), gl.GL_COLOR_BUFFER_BIT),
    FramebufferAttachment.DEPTH: gl.GL_DEPTH_BUFFER_BIT,
    FramebufferAttachment.STENCIL: gl.GL_STENCIL_BUFFER_BIT,
    FramebufferAttachment.DEPTH_STENCIL: gl.GL_DEPTH_BUFFER_BIT | gl.GL_STENCIL_BUFFER_BIT,
}


def get_viewport() -> tuple:
    """Get the current OpenGL viewport dimensions (left, bottom, right, top)."""
    ctx = pyglet.graphics.api.core.current_context
    return tuple(ctx.gl.getParameter(gl.GL_VIEWPORT).to_py())


def get_screenshot() -> ImageData:
    """Read the pixel data from the default color buffer into ImageData.

    This provides a simplistic screenshot of the default frame buffer.

    This may be inaccurate if you utilize multiple frame buffers in your program.

    .. versionadded:: 3.0
    """
    ctx = pyglet.graphics.api.core.current_context
    _gl = ctx.gl

    width = _gl.drawingBufferWidth
    height = _gl.drawingBufferHeight
    fmt = 'RGBA'

    size = len(fmt) * width * height
    buf = js.Uint8Array.new(size)

    _gl.readPixels(0, 0, width, height, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, buf)

    return ImageData(width, height, fmt, buf)


class WebGLRenderbuffer(RenderbufferResource):
    """OpenGL Renderbuffer Object."""

    def __init__(self, context: OpenGLSurfaceContext, width: int, height: int,
                 component_format: ComponentFormat, bit_size: int, data_type: DataTypes = "I", samples: int = 1) -> None:
        """Create a RenderBuffer instance."""
        RenderbufferResource.__init__(self)
        self._context = context or pyglet.graphics.api.core.current_context
        self._gl = self._context.gl
        self._width = width
        self._height = height
        self._internal_format = _get_internal_format(component_format, bit_size, data_type)

        self._id = self._gl.createRenderbuffer()
        self._handle = self._id
        self.bind()

        if samples > 1:
            self._gl.renderbufferStorageMultisample(
                gl.GL_RENDERBUFFER,
                samples,
                self._internal_format,
                width,
                height,
            )
        else:
            self._gl.renderbufferStorage(
                gl.GL_RENDERBUFFER,
                self._internal_format,
                width,
                height,
            )

        self.unbind()

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def bind(self) -> None:
        self._gl.bindRenderbuffer(gl.GL_RENDERBUFFER, self._id)

    def unbind(self) -> None:
        self._gl.bindRenderbuffer(gl.GL_RENDERBUFFER, None)

    def delete(self) -> None:
        if self._id is not None:
            self._gl.deleteRenderbuffer(self._id)   # FIX for WebGL
            self._id = None
            self._handle = None

    def __del__(self) -> None:
        self.delete()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(handle={self._handle})"


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

class WebGLFramebuffer(FramebufferResource):
    """OpenGL Framebuffer Object.

    .. versionadded:: 2.0
    """
    _id: WebGLFramebufferObject | None

    def __init__(self,
                 target: FramebufferTarget = FramebufferTarget.FRAMEBUFFER,
                 context: OpenGLSurfaceContext | None = None) -> None:
        FramebufferResource.__init__(self)
        self._context = context or pyglet.graphics.api.core.current_context
        self._gl = self._context.gl
        self._id = self._gl.createFramebuffer()
        self._handle = self._id
        self._clear_bits = 0
        self._gl_attachment_types = []
        self._width = 0
        self._height = 0
        self._binding_stack: list[tuple[WebGLFramebufferObject | None, ...]] = []
        self.target = target
        self._gl_target = _gl_target_map[target]

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
        self._gl.bindFramebuffer(self._gl_target, self._id)

    def unbind(self) -> None:
        """Unbind the Framebuffer.

        Unbind should be called to prevent further rendering
        to the framebuffer, or if you wish to access data
        from its Texture atachments.
        """
        self._gl.bindFramebuffer(self._gl_target, None)

    def __enter__(self) -> WebGLFramebuffer:  # noqa: PYI034
        if self.target == FramebufferTarget.FRAMEBUFFER:
            self._binding_stack.append((
                self._gl.getParameter(gl.GL_DRAW_FRAMEBUFFER_BINDING),
                self._gl.getParameter(gl.GL_READ_FRAMEBUFFER_BINDING),
            ))
            self.bind()
            return self

        binding_enum = {
            FramebufferTarget.DRAW: gl.GL_DRAW_FRAMEBUFFER_BINDING,
            FramebufferTarget.READ: gl.GL_READ_FRAMEBUFFER_BINDING,
        }[self.target]
        self._binding_stack.append((self._gl.getParameter(binding_enum),))
        self.bind()
        return self

    def __exit__(self, *_args: object) -> None:
        bindings = self._binding_stack.pop()
        if len(bindings) == 2:
            self._gl.bindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, bindings[0])
            self._gl.bindFramebuffer(gl.GL_READ_FRAMEBUFFER, bindings[1])
        else:
            self._gl.bindFramebuffer(self._gl_target, bindings[0])

    def clear(self, color: tuple[float, float, float, float] | None = None) -> None:
        """Clear the attachments, optionally using a temporary clear color."""
        if self._clear_bits:
            previous_color = None
            if color is not None:
                previous_color = tuple(self._gl.getParameter(gl.GL_COLOR_CLEAR_VALUE).to_py())
                self._gl.clearColor(*color)
            try:
                with self:
                    self._gl.clear(self._clear_bits)
            finally:
                if previous_color is not None:
                    self._gl.clearColor(*previous_color)

    def delete(self) -> None:
        """Explicitly delete the Framebuffer."""
        if self._id is not None:
            self._gl.deleteFramebuffer(self._id)
            self._id = None
            self._handle = None

    def __del__(self) -> None:
        self.delete()

    @property
    def is_complete(self) -> bool:
        """True if the framebuffer is 'complete', else False."""
        return self._gl.checkFramebufferStatus(self._gl_target) == gl.GL_FRAMEBUFFER_COMPLETE

    def get_status(self) -> str:
        """Get the current Framebuffer status, as a string.

        If ``Framebuffer.is_complete`` is ``False``, this method
        can be used for more information. It will return a
        string with the OpenGL reported status.
        """
        gl_status = self._gl.checkFramebufferStatus(self._gl_target)

        return _status_states.get(gl_status, "Unknown error")

    def attach_texture(self, texture: WebGLTexture, attachment: FramebufferAttachment = FramebufferAttachment.COLOR0,
                       level: int = 0) -> None:
        """Attach a Texture to the Framebuffer.

        Args:
            texture:
                Specifies the texture object to attach to the framebuffer attachment
                point named by attachment.
            attachment:
                Specifies the attachment point of the framebuffer.
            level:
                The mipmap level of the targeted texture to attach to the framebuffer.
        """
        self.bind()
        gl_attachment = _gl_attachment_map[attachment]
        self._gl.framebufferTexture2D(
            self._gl_target,
            gl_attachment,
            gl.GL_TEXTURE_2D,
            texture.handle,
            level,
        )
        self._clear_bits |= _clear_bit_map[attachment]
        self._gl_attachment_types.append(gl_attachment)
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_texture_layer(self, texture: WebGLTexture, layer: int, level: int,
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
        self._gl.framebufferTextureLayer(
            self._gl_target,
            gl_attachment,
            texture.handle,
            level,
            layer,
        )
        self._clear_bits |= _clear_bit_map[attachment]
        self._gl_attachment_types.append(gl_attachment)
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_renderbuffer(self, renderbuffer: WebGLRenderbuffer,
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
        self._gl.framebufferRenderbuffer(
            self._gl_target,
            gl_attachment,
            gl.GL_RENDERBUFFER,
            renderbuffer.handle,
        )
        self._gl_attachment_types.append(gl_attachment)
        self._clear_bits |= _clear_bit_map[attachment]
        self._width = max(renderbuffer.width, self._width)
        self._height = max(renderbuffer.height, self._height)
        self.unbind()

    def set_draw_buffers(self) -> None:
        """Enable multiple render targets for the FBO (WebGL2)."""
        self.bind()
        self._gl.drawBuffers(self._gl_attachment_types)
        self.unbind()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id})"
