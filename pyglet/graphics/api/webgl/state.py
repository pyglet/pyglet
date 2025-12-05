from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Generator

from pyglet.enums import BlendFactor, BlendOp, CompareOp
from pyglet.graphics.api.webgl.enums import blend_factor_map, compare_op_map
from pyglet.graphics.api.webgl.gl import GL_BLEND, GL_DEPTH_TEST, GL_SCISSOR_TEST, GL_TEXTURE0
from pyglet.graphics.state import State

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl.webgl_js import WebGLTexture
    from pyglet.graphics.api.webgl import OpenGLSurfaceContext
    from pyglet.graphics import Group
    from pyglet.graphics.api.webgl.shader import ShaderProgram
    from pyglet.graphics.texture import TextureBase


@dataclass(frozen=True)
class ActiveTextureState(State):
    binding: int
    sets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.activeTexture(GL_TEXTURE0 + self.binding)

    # Technically not needed since this is a dependent state and will always be called with its parents.
    # def unset_state(self, ctx: OpenGLSurfaceContext):
    #    glActiveTexture(GL_TEXTURE0)


@dataclass(frozen=True)
class TextureState(State):  # noqa: D101
    texture: tuple[int, int]
    # WebGL doesn't expose the actual texture ID, so we use the python memory ID instead to consolidate the types
    # as Python doesn't allow the JS Proxy to be hashable.
    # However, the actual WebGL object needs to be passed for the function.
    webgl_texture: WebGLTexture = field(hash=False, compare=False)
    binding: int = 0
    set_id: int = 0

    parents: bool = True
    sets_state: bool = True

    @classmethod
    def from_texture(cls, texture: TextureBase, binding: int, set_id: int) -> TextureState:
        return cls((texture.target, id(texture.id)),
                   webgl_texture=texture.id,
                   binding=binding,
                   set_id=set_id)

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.bindTexture(self.texture[0], self.webgl_texture)

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
    #    self.program.stop()l


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
        ctx.gl.enable(GL_SCISSOR_TEST)

    def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.disable(GL_SCISSOR_TEST)


@dataclass(frozen=True)
class ScissorState(State):
    group: Group

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield ScissorStateEnable()

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.scissor(*self.group.data["scissor"])


@dataclass(frozen=True)
class BlendStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.enable(GL_BLEND)

    def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.disable(GL_BLEND)


@dataclass(frozen=True)
class BlendState(State):
    src: BlendFactor
    dst: BlendFactor
    op: BlendOp = BlendOp.ADD

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield BlendStateEnable()
        # Do later.
        # if self.op != BlendOp.ADD:
        #    yield GLBlendState(blend_factor_map[self.src], self.op)

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.blendFunc(blend_factor_map[self.src], blend_factor_map[self.dst])


@dataclass(frozen=True)
class DepthTestStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.enable(GL_DEPTH_TEST)

    def unset_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.disable(GL_DEPTH_TEST)


@dataclass(frozen=True)
class DepthBufferComparison(State):
    func: CompareOp

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield DepthTestStateEnable()

    def set_state(self, ctx: OpenGLSurfaceContext) -> None:
        ctx.gl.depthFunc(compare_op_map[self.func])


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
        ctx.gl.viewport(self.x, self.y, self.width, self.height)


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

