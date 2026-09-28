from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, Generator

from pyglet.enums import BlendFactor, BlendOp, CompareOp, CullFace, FrontFace, StencilOp
from pyglet.graphics.api.webgl.enums import (
    blend_factor_map, blend_op_map, compare_op_map, cull_face_map, front_face_map, stencil_op_map,
)
from pyglet.graphics.api.webgl.gl import (
    GL_BLEND,
    GL_CULL_FACE,
    GL_DEPTH_TEST,
    GL_POLYGON_OFFSET_FILL,
    GL_SCISSOR_TEST,
    GL_SAMPLE_COVERAGE,
    GL_STENCIL_BUFFER_BIT,
    GL_STENCIL_TEST,
    GL_TEXTURE0,
)
from pyglet.graphics.state import State, ViewportProtocol, _BaseScissorState, _BaseViewportState

if TYPE_CHECKING:
    from pyglet.customtypes import ScissorProtocol
    from pyglet.graphics.buffer import UniformBufferRegion
    from pyglet.graphics.api.webgl.shader import ShaderProgram
    from pyglet.graphics.draw import DrawContext
    from pyglet.graphics.texture import Texture
    from pyglet.graphics.resource import TextureKey


@dataclass(frozen=True)
class ActiveTextureState(State):
    binding: int
    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.activeTexture(GL_TEXTURE0 + self.binding)


@dataclass(frozen=True)
class TextureState(State):  # noqa: D101
    texture: tuple[int, TextureKey]
    handle: Any = field(hash=False, compare=False)
    binding: int = 0
    set_id: int = 0

    parents: bool = True
    sets_state: bool = True

    @classmethod
    def from_texture(cls, texture: Texture, binding: int, set_id: int) -> TextureState:
        return cls((texture.target, texture.key),
                   handle=texture.handle,
                   binding=binding,
                   set_id=set_id)

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.bindTexture(self.texture[0], self.handle)

    def generate_parent_states(self) -> Generator[State, None, None]:
        yield ActiveTextureState(self.binding)


@dataclass(frozen=True)
class MultiTextureSamplerState(State):
    """Texture bindings and sampler uniforms for multi-texture draws."""
    program: ShaderProgram
    textures: tuple[tuple[tuple[int, TextureKey], int, int], ...]
    uniforms: tuple[tuple[str, int], ...]
    handles: tuple[Any, ...] = field(hash=False, compare=False)

    sets_state: bool = True
    unsets_state: bool = True

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
            ctx.surface_ctx.gl.activeTexture(GL_TEXTURE0 + texture_unit)
            ctx.surface_ctx.gl.bindTexture(texture[0], handle)

        for uniform_name, texture_unit in self.uniforms:
            self.program[uniform_name] = texture_unit

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.activeTexture(GL_TEXTURE0)


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
        ctx.surface_ctx.gl.blendEquation(blend_op_map[self.op])


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
    flag: bool

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.depthMask(self.flag)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.depthMask(not self.flag)


@dataclass(frozen=True)
class DepthRangeState(State):
    near: float
    far: float

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.depthRange(self.near, self.far)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.depthRange(0.0, 1.0)


@dataclass(frozen=True)
class PolygonOffsetState(State):
    factor: float
    units: float

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.enable(GL_POLYGON_OFFSET_FILL)
        ctx.surface_ctx.gl.polygonOffset(self.factor, self.units)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.disable(GL_POLYGON_OFFSET_FILL)


@dataclass(frozen=True)
class SampleCoverageState(State):
    value: float
    invert: bool = False

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.enable(GL_SAMPLE_COVERAGE)
        ctx.surface_ctx.gl.sampleCoverage(self.value, self.invert)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.disable(GL_SAMPLE_COVERAGE)


@dataclass(frozen=True)
class CullFaceState(State):
    face: CullFace

    sets_state: bool = True
    unsets_state: bool = True
    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.enable(GL_CULL_FACE)
        ctx.surface_ctx.gl.cullFace(cull_face_map[self.face])

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.disable(GL_CULL_FACE)


@dataclass(frozen=True)
class FrontFaceState(State):
    face: FrontFace

    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.frontFace(front_face_map[self.face])


@dataclass(frozen=True)
class StencilTestState(State):
    enabled: bool

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        (ctx.surface_ctx.gl.enable if self.enabled else ctx.surface_ctx.gl.disable)(GL_STENCIL_TEST)

    def unset_state(self, ctx: DrawContext) -> None:
        (ctx.surface_ctx.gl.disable if self.enabled else ctx.surface_ctx.gl.enable)(GL_STENCIL_TEST)


@dataclass(frozen=True)
class StencilMaskState(State):
    mask: int

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.stencilMask(self.mask)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.stencilMask(0xFF)


@dataclass(frozen=True)
class StencilFuncState(State):
    func: CompareOp
    ref: int
    mask: int

    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.stencilFunc(compare_op_map[self.func], self.ref, self.mask)


@dataclass(frozen=True)
class StencilOpState(State):
    fail: StencilOp
    z_fail: StencilOp
    z_pass: StencilOp

    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.stencilOp(
            stencil_op_map[self.fail], stencil_op_map[self.z_fail], stencil_op_map[self.z_pass],
        )


@dataclass(frozen=True)
class ColorMaskState(State):
    red: bool
    green: bool
    blue: bool
    alpha: bool

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.colorMask(self.red, self.green, self.blue, self.alpha)

    def unset_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.colorMask(True, True, True, True)


@dataclass(frozen=True)
class StencilClearState(State):
    sets_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.surface_ctx.gl.clear(GL_STENCIL_BUFFER_BIT)


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
