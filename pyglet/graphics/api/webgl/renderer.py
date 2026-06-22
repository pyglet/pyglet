from __future__ import annotations

from typing import Any

from pyglet.graphics.api.base import BackendRenderer
from pyglet.graphics.api.webgl.gl import GL_SCISSOR_TEST


class WebGLRenderer(BackendRenderer):
    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        self.surface_ctx.gl.viewport(x, y, width, height)

    def set_scissor(self, scissor: Any | None) -> None:
        if scissor is None:
            self.surface_ctx.gl.disable(GL_SCISSOR_TEST)
            return

        x, y, width, height = scissor.area
        self.surface_ctx.gl.enable(GL_SCISSOR_TEST)
        self.surface_ctx.gl.scissor(int(x), int(y), int(width), int(height))

    def set_clear_color(self, r: float, g: float, b: float, a: float) -> None:
        self.surface_ctx._clear_color = (r, g, b, a)
