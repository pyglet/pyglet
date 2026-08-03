"""OpenGL 2 and OpenGL ES 2 texture pixel readback helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.graphics.api.gl.pixel import GLPixelReadback

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.framebuffer import GLFramebuffer


class GL2PixelReadback(GLPixelReadback):
    """Pixel readback using OpenGL 2-compatible framebuffer state."""

    def get_framebuffer(self) -> GLFramebuffer:
        """Return the lazily created OpenGL 2 framebuffer used for readback."""
        if self._framebuffer is None:
            from pyglet.graphics.api.gl2.framebuffer import GL2Framebuffer  # noqa: PLC0415

            self._framebuffer = GL2Framebuffer(context=self._context)
        return self._framebuffer
