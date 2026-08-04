"""OpenGL texture pixel readback helpers."""

from __future__ import annotations

from contextlib import contextmanager
from ctypes import sizeof
from typing import TYPE_CHECKING, Iterator

from pyglet.customtypes import Buffer
from pyglet.graphics import GraphicsAPIError
from pyglet.graphics.api.base import PixelReadback
from pyglet.graphics.api.gl import gl

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.context import OpenGLSurfaceContext
    from pyglet.graphics.api.gl.framebuffer import GLFramebuffer
    from pyglet.graphics.api.gl.texture import GLTexture


class GLPixelReadback(PixelReadback):
    """Context-owned resources and state handling for texture readback."""

    def __init__(self, context: OpenGLSurfaceContext) -> None:
        """Create a readback helper for an OpenGL surface context."""
        super().__init__(context)
        self._framebuffer: GLFramebuffer | None = None

    def get_framebuffer(self) -> GLFramebuffer:
        """Return the lazily created framebuffer used for GLES readback."""
        if self._framebuffer is None:
            from pyglet.graphics.api.gl.framebuffer import GLFramebuffer  # noqa: PLC0415

            self._framebuffer = GLFramebuffer(context=self._context)
        return self._framebuffer

    @contextmanager
    def _pack_state(self) -> Iterator[None]:
        alignment = gl.GLint()
        self._context.glGetIntegerv(gl.GL_PACK_ALIGNMENT, alignment)
        self._context.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
        try:
            yield
        finally:
            self._context.glPixelStorei(gl.GL_PACK_ALIGNMENT, alignment.value)

    def read_texture(self, texture: GLTexture, z: int, level: int,
                     gl_format: int, gl_type: int, component_type: type,
                     components: int) -> tuple[int, int, Buffer]:
        """Read one texture image or layer into tightly packed CPU memory."""
        width, height, depth = texture._get_mipmap_dimensions(level)
        if not 0 <= z < depth:
            msg = f"Texture layer {z} is outside the valid range 0..{depth - 1}."
            raise ValueError(msg)

        layer_elements = width * height * components
        direct_readback = self._context.info.pixel_transfer.direct_texture_readback

        with self._pack_state():
            if direct_readback:
                buffer = (component_type * (layer_elements * depth))()
                self._context.glBindTexture(texture.target, texture.id)
                self._context.glGetTexImage(texture.target, level, gl_format, gl_type, buffer)

                if depth == 1:
                    data = buffer
                else:
                    start = z * layer_elements
                    data = (component_type * layer_elements).from_buffer(
                        buffer, start * sizeof(component_type),
                    )
            else:
                buffer = (component_type * layer_elements)()
                framebuffer = self.get_framebuffer()
                with framebuffer:
                    texture._set_readback_framebuffer_attachment(texture.id, z, level)
                    try:
                        if not framebuffer.is_complete:
                            msg = f"Texture cannot be read through a framebuffer: {framebuffer.get_status()}"
                            raise GraphicsAPIError(msg)
                        self._context.glReadPixels(0, 0, width, height, gl_format, gl_type, buffer)
                    finally:
                        texture._set_readback_framebuffer_attachment(0, z, level)
                data = buffer

        return width, height, data
