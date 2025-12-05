from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Generator, TYPE_CHECKING

import pyglet
from pyglet.enums import BlendFactor, BlendOp, CompareOp
from pyglet.graphics.api.gl import GL_TEXTURE0, GL_BLEND, GL_SCISSOR_TEST, GL_DEPTH_TEST, OpenGLSurfaceContext, \
    glScissor
from pyglet.graphics.api.gl.enums import blend_factor_map, compare_op_map
from pyglet.graphics.state import State

if TYPE_CHECKING:
    from pyglet.graphics.texture import TextureBase
    from pyglet.graphics.api.gl.shader import ShaderProgram
    from pyglet.customtypes import ScissorProtocol


@dataclass(frozen=True)
class ActiveTextureState(State):
    binding: int
    sets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx = pyglet.graphics.api.core.current_context
        ctx.glActiveTexture(GL_TEXTURE0 + self.binding)

    # Technically not needed since this is a dependent state and will always be called with its parents.
    # def unset_state(self, ctx: OpenGLSurfaceContext):
    #    glActiveTexture(GL_TEXTURE0)


@dataclass(frozen=True)
class TextureState(State):  # noqa: D101
    texture: tuple[int, int]
    binding: int = 0
    set_id: int = 0

    parents: bool = True
    sets_state: bool = True

    @classmethod
    def from_texture(cls, texture: TextureBase, binding: int, set_id: int) -> TextureState:
        return cls((texture.target, texture.id), binding, set_id)

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glBindTexture(*self.texture)

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield ActiveTextureState(self.binding)



@dataclass(frozen=True)
class ShaderProgramState(State):
    program: ShaderProgram

    sets_state: bool = True
    #unsets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        self.program.use()

    #def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
    #    self.program.stop()

@dataclass(frozen=True)
class RenderPassState(State):
    renderpass: Any  # Renderpass for Vulkan.


@dataclass(frozen=True)
class RenderAreaState(State):
    width: int
    height: int


@dataclass(frozen=True)
class ScissorStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glEnable(GL_SCISSOR_TEST)

    def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glDisable(GL_SCISSOR_TEST)

@dataclass(frozen=True)
class ScissorState(State):
    spo: ScissorProtocol

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield ScissorStateEnable()

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        glScissor(int(self.spo.x), int(self.spo.y), int(self.spo.width), int(self.spo.height))


@dataclass(frozen=True)
class BlendStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glEnable(GL_BLEND)

    def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glDisable(GL_BLEND)


@dataclass(frozen=True)
class BlendState(State):
    src: BlendFactor
    dst: BlendFactor
    op: BlendOp = BlendOp.ADD

    sets_state: bool = True
    parents: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.src, BlendFactor):
            raise Exception("src must be BlendFactor")

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield BlendStateEnable()
        # Do later.
        #if self.op != BlendOp.ADD:
        #    yield GLBlendState(blend_factor_map[self.src], self.op)

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glBlendFunc(blend_factor_map[self.src], blend_factor_map[self.dst])


@dataclass(frozen=True)
class DepthTestStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glEnable(GL_DEPTH_TEST)

    def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glDisable(GL_DEPTH_TEST)


@dataclass(frozen=True)
class DepthBufferComparison(State):
    func: CompareOp

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield DepthTestStateEnable()

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glDepthFunc(compare_op_map[self.func])


@dataclass(frozen=True)
class DepthWriteState(State):
    flag: int

@dataclass(frozen=True)
class StencilFuncState(State):
    func: Callable
    ref: int
    mask: int

@dataclass(frozen=True)
class StencilOpState(State):
    fail: int
    zfail: int
    zpass: int

@dataclass(frozen=True)
class PolygonModeState(State):
    face: int
    mode: int


@dataclass(frozen=True)
class ViewportState(State):
    x: int
    y: int
    width: int
    height: float

    sets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.glViewport(self.x, self.y, self.width, self.height)


@dataclass(frozen=True)
class UniformBufferState(State):
    name: str
    binding: int


@dataclass(frozen=True)
class ShaderUniformState(State):
    program: ShaderProgram
    data: dict[str, Any]

    sets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        for name, value in self.data.items():
            self.program[name] = value

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: State) -> bool:
        return False
