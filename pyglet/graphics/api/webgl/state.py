from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, Callable, Generator

from pyglet.enums import BlendFactor, BlendOp, CompareOp
from pyglet.graphics.api.webgl.enums import blend_factor_map, compare_op_map
from pyglet.graphics.api.webgl.gl import GL_BLEND, GL_DEPTH_TEST, GL_SCISSOR_TEST, GL_TEXTURE0
from pyglet.graphics.state import State, _BaseScissorState, _BaseViewportState

if TYPE_CHECKING:
    from pyglet.customtypes import ScissorProtocol
    from pyglet.graphics.buffer import UniformBufferRegion
    from pyglet.graphics.api.webgl.shader import ShaderProgram
    from pyglet.graphics.draw import DrawContext
    from pyglet.graphics.texture import Texture


@dataclass(frozen=True)
class ActiveTextureState(State):
    binding: int
    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.activeTexture(GL_TEXTURE0 + self.binding)


@dataclass(frozen=True)
class TextureState(State):  # noqa: D101
    texture: tuple[int, int]
    # WebGL doesn't expose the actual texture ID, so we use the python memory ID instead to consolidate the types
    # as Python doesn't allow the JS Proxy to be hashable.
    # However, the actual WebGL object needs to be passed for the function.
    webgl_texture: Any = field(hash=False, compare=False)
    binding: int = 0
    set_id: int = 0

    parents: bool = True
    sets_state: bool = True

    @classmethod
    def from_texture(cls, texture: Texture, binding: int, set_id: int) -> TextureState:
        return cls((texture.target, id(texture.id)),
                   webgl_texture=texture.id,
                   binding=binding,
                   set_id=set_id)

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.bindTexture(self.texture[0], self.webgl_texture)

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield ActiveTextureState(self.binding)


@dataclass(frozen=True)
class MultiTextureSamplerState(State):
    """Texture bindings and sampler uniforms for multi-texture draws."""
    program: ShaderProgram
    textures: tuple[tuple[tuple[int, int], int, int], ...]
    uniforms: tuple[tuple[str, int], ...]
    webgl_textures: tuple[Any, ...] = field(hash=False, compare=False)

    sets_state: bool = True

    @classmethod
    def from_textures(
            cls,
            program: ShaderProgram,
            textures: dict[str, Texture],
            first_texture_unit: int = 0,
            set_id: int = 0) -> MultiTextureSamplerState:
        texture_states = tuple(
            ((texture.target, id(texture.id)), texture_unit, set_id)
            for texture_unit, texture in enumerate(textures.values(), first_texture_unit)
        )
        uniforms = tuple((name, idx) for idx, name in enumerate(textures, first_texture_unit))
        webgl_textures = tuple(texture.id for texture in textures.values())
        return cls(program, texture_states, uniforms, webgl_textures)

    def set_state(self, ctx: DrawContext) -> None:
        for (texture, texture_unit, _set_id), webgl_texture in zip(self.textures, self.webgl_textures):
            ctx.surface_ctx.gl.activeTexture(GL_TEXTURE0 + texture_unit)
            ctx.surface_ctx.gl.bindTexture(texture[0], webgl_texture)

        for uniform_name, texture_unit in self.uniforms:
            self.program[uniform_name] = texture_unit


@dataclass(frozen=True)
class ShaderProgramState(State):
    program: ShaderProgram

    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        self.program.use()
        ctx.active_shader_program = self.program


@dataclass(frozen=True)
class RenderPassState(State):
    renderpass: Any  # Renderpass for Vulkan.


@dataclass(frozen=True)
class RenderAreaState(State):
    width: int
    height: int


@dataclass(frozen=True)
class ScissorState(_BaseScissorState):
    scissor: ScissorProtocol
    owned_by_camera: bool = False

    sets_state: bool = True
    unsets_state: bool = True
    enforced_state: bool = True

    def apply_to_backend(self, ctx: DrawContext) -> None:
        ctx.apply_scissor()


@dataclass(frozen=True)
class BlendStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.enable(GL_BLEND)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.disable(GL_BLEND)


@dataclass(frozen=True)
class BlendState(State):
    src: BlendFactor
    dst: BlendFactor
    op: BlendOp = BlendOp.ADD

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield BlendStateEnable()

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.blendFunc(blend_factor_map[self.src], blend_factor_map[self.dst])


@dataclass(frozen=True)
class DepthTestStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.enable(GL_DEPTH_TEST)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.disable(GL_DEPTH_TEST)


@dataclass(frozen=True)
class DepthBufferComparison(State):
    func: CompareOp

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield DepthTestStateEnable()

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.depthFunc(compare_op_map[self.func])


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
class ViewportState(_BaseViewportState):
    x: int
    y: int
    width: int
    height: int

    sets_state: bool = True
    unsets_state: bool = True
    enforced_state: bool = True

    def apply_to_backend(self, ctx: DrawContext) -> None:
        ctx.apply_viewport()


@dataclass(frozen=True)
class UniformBufferState(State):
    region: UniformBufferRegion
    binding_index: int | None = None

    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        self.region.bind(binding_index=self.binding_index)


@dataclass(frozen=True)
class ShaderUniformState(State):
    program: ShaderProgram
    data: dict[str, Any]

    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        for name, value in self.data.items():
            self.program[name] = value

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: State) -> bool:
        return False
