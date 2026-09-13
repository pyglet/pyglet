from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generator, TYPE_CHECKING

from pyglet.enums import BlendFactor, BlendOp, CompareOp
from pyglet.graphics.api.gl import GL_BLEND, GL_DEPTH_TEST, GL_SCISSOR_TEST, GL_TEXTURE0
from pyglet.graphics.api.gl.enums import blend_factor_map, compare_op_map
from pyglet.graphics.state import (
    State,
    ViewportProtocol,
    _BaseScissorState,
    _BaseViewportState,
)

if TYPE_CHECKING:
    from pyglet.customtypes import ScissorProtocol
    from pyglet.graphics.draw import DrawContext
    from pyglet.graphics.api.gl.shader import ShaderProgram
    from pyglet.graphics.buffer import UniformBufferRegion
    from pyglet.graphics.texture import Texture
    from pyglet.graphics.resource import TextureKey


@dataclass(frozen=True)
class ActiveTextureState(State):
    binding: int
    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glActiveTexture(GL_TEXTURE0 + self.binding)


@dataclass(frozen=True)
class TextureState(State):  # noqa: D101
    texture: tuple[int, TextureKey]
    handle: int = field(hash=False, compare=False)
    binding: int = 0
    set_id: int = 0

    parents: bool = True
    sets_state: bool = True

    @classmethod
    def from_texture(cls, texture: Texture, binding: int, set_id: int) -> TextureState:
        return cls((texture.target, texture.key), texture.handle, binding, set_id)

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glBindTexture(self.texture[0], self.handle)

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield ActiveTextureState(self.binding)


@dataclass(frozen=True)
class MultiTextureSamplerState(State):
    """Texture bindings and sampler uniforms for multi-texture draws."""
    program: ShaderProgram
    textures: tuple[tuple[tuple[int, TextureKey], int, int], ...]
    uniforms: tuple[tuple[str, int], ...]
    handles: tuple[int, ...] = field(hash=False, compare=False)

    sets_state: bool = True

    @classmethod
    def from_textures(
            cls,
            program: ShaderProgram,
            textures: dict[str, Texture],
            first_texture_unit: int = 0,
            set_id: int = 0) -> MultiTextureSamplerState:
        texture_states = tuple(
            ((texture.target, texture.key), texture_unit, set_id)
            for texture_unit, texture in enumerate(textures.values(), first_texture_unit)
        )
        uniforms = tuple((name, idx) for idx, name in enumerate(textures, first_texture_unit))
        handles = tuple(texture.handle for texture in textures.values())
        return cls(program, texture_states, uniforms, handles)

    def set_state(self, ctx: DrawContext) -> None:
        for (texture, texture_unit, _set_id), handle in zip(self.textures, self.handles):
            ctx.surface_ctx.glActiveTexture(GL_TEXTURE0 + texture_unit)
            ctx.surface_ctx.glBindTexture(texture[0], handle)

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
class ScissorStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glEnable(GL_SCISSOR_TEST)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glDisable(GL_SCISSOR_TEST)


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
        ctx.surface_ctx.glEnable(GL_BLEND)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glDisable(GL_BLEND)


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

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glBlendFunc(blend_factor_map[self.src], blend_factor_map[self.dst])


@dataclass(frozen=True)
class DepthTestStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glEnable(GL_DEPTH_TEST)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glDisable(GL_DEPTH_TEST)


@dataclass(frozen=True)
class DepthBufferComparison(State):
    func: CompareOp

    sets_state: bool = True
    parents: bool = True

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield DepthTestStateEnable()

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.glDepthFunc(compare_op_map[self.func])


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


@dataclass(frozen=True, eq=False)
class ViewportState(_BaseViewportState):
    viewport: ViewportProtocol

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


