from __future__ import annotations

from dataclasses import dataclass

from pyglet.graphics.state import State
from typing import TYPE_CHECKING
from pyglet.graphics.api.gl.state import (TextureState, MultiTextureSamplerState, BlendState, ShaderUniformState,   # noqa: F401
                                          DepthBufferComparison, ScissorState, ViewportState)


if TYPE_CHECKING:
    from pyglet.graphics.draw import DrawContext
    from pyglet.graphics import ShaderProgram


@dataclass(frozen=True)
class ShaderProgramState(State):
    program: ShaderProgram

    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        self.program.use()
        ctx.active_shader_program = self.program

        if ctx.active_camera and ctx.active_camera.view.storage:
            ctx.active_camera.view.storage.bind(ctx)


