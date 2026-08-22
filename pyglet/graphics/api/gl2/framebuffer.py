"""OpenGL 2 framebuffer implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.enums import FramebufferAttachment, FramebufferTarget
from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl.framebuffer import (
    GLFramebuffer,
    GLRenderbuffer,
    _clear_bit_map,
    _gl_attachment_map,
    get_screenshot,
    get_viewport,
)

if TYPE_CHECKING:
    from pyglet.graphics.api.gl import OpenGLSurfaceContext
    from pyglet.graphics.api.gl.texture import GLTexture


class GL2Framebuffer(GLFramebuffer):
    """Framebuffer implementation for OpenGL 2 and OpenGL ES 2."""

    def __init__(
        self,
        target: FramebufferTarget = FramebufferTarget.FRAMEBUFFER,
        context: OpenGLSurfaceContext | None = None,
    ) -> None:
        """Create an OpenGL 2 framebuffer."""
        if target != FramebufferTarget.FRAMEBUFFER:
            raise ValueError("OpenGL 2 framebuffers only support FramebufferTarget.FRAMEBUFFER.")
        super().__init__(target, context)

    def __enter__(self) -> GL2Framebuffer:  # noqa: PYI034
        binding = gl.GLint()
        self._context.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING, binding)
        self._binding_stack.append((binding.value,))
        self.bind()
        return self

    def __exit__(self, *_args: object) -> None:
        self._context.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._binding_stack.pop()[0])

    def attach_texture(
        self,
        texture: GLTexture,
        attachment: FramebufferAttachment = FramebufferAttachment.COLOR0,
        level: int = 0,
    ) -> None:
        """Attach a two-dimensional texture to this framebuffer."""
        self.bind()
        gl_attachment = _gl_attachment_map[attachment]
        self._context.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER,
            gl_attachment,
            texture.target,
            texture.handle,
            level,
        )
        self._clear_bits |= _clear_bit_map[attachment]
        self._width = max(texture.width, self._width)
        self._height = max(texture.height, self._height)
        self.unbind()

    def attach_texture_layer(
        self,
        texture: GLTexture,
        layer: int,
        level: int,
        attachment: FramebufferAttachment = FramebufferAttachment.COLOR0,
    ) -> None:
        """Reject layered attachments, which OpenGL 2 does not support."""
        raise NotImplementedError("Layered framebuffer texture attachments require OpenGL 3.")


__all__ = (
    "GL2Framebuffer",
    "GLRenderbuffer",
    "get_screenshot",
    "get_viewport",
)
