from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, TYPE_CHECKING, Sequence

from pyglet.enums import BlendFactor, BlendOp
from pyglet.graphics.api.gl import glBindTexture, glActiveTexture, GL_TEXTURE0, glBlendFunc, glEnable, GL_BLEND, \
    glDisable, glScissor, glViewport, GL_SCISSOR_TEST
from pyglet.graphics.api.gl.enums import blend_factor_map
from pyglet.graphics.state import State

if TYPE_CHECKING:
    from pyglet.graphics import Group
    from pyglet.image.base import TextureBase
    from pyglet.graphics.api.gl.shader import ShaderProgram


@dataclass(frozen=True)
class ActiveTextureState(State):
    binding: int
    sets_state: bool = True

    def set_state(self):
        glActiveTexture(GL_TEXTURE0 + self.binding)

    # Technically not needed since this is a dependent state and will always be called with its parents.
    # def unset_state(self):
    #    glActiveTexture(GL_TEXTURE0)


@dataclass(frozen=True)
class TextureState(State):  # noqa: D101
    texture: TextureBase
    binding: int = 0
    set_id: int = 0

    dependents: bool = True
    sets_state: bool = True

    def set_state(self) -> None:
        glBindTexture(self.texture.target, self.texture.id)

    def generate_dependent_states(self) -> Generator[State, None, None]:
        yield ActiveTextureState(self.binding)



@dataclass(frozen=True)
class ShaderProgramState(State):
    program: ShaderProgram

    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self) -> None:
        self.program.use()

    def unset_state(self) -> None:
        self.program.stop()

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

    def set_state(self) -> None:
        glEnable(GL_SCISSOR_TEST)

    def unset_state(self) -> None:
        glDisable(GL_SCISSOR_TEST)

@dataclass(frozen=True)
class ScissorState(State):
    x: int
    y: int
    width: int
    height: int

    sets_state: bool = True

    def generate_dependent_states(self) -> Generator[State, None, None]:
        yield ScissorStateEnable()

    def set_state(self) -> None:
        glScissor(self.x, self.y, self.width, self.height)


@dataclass(frozen=True)
class BlendStateEnable(State):
    sets_state: bool = True
    unsets_state: bool = True

    def set_state(self) -> None:
        glEnable(GL_BLEND)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)


@dataclass(frozen=True)
class BlendState(State):
    src: BlendFactor
    dst: BlendFactor
    op: BlendOp = BlendOp.ADD

    sets_state: bool = True
    dependents: bool = True

    def generate_dependent_states(self) -> Generator[State, None, None]:
        yield BlendStateEnable()
        # Do later.
        #if self.op != BlendOp.ADD:
        #    yield GLBlendState(blend_factor_map[self.src], self.op)

    def set_state(self) -> None:
        glBlendFunc(blend_factor_map[self.src], blend_factor_map[self.dst])


@dataclass(frozen=True)
class DepthTestState(State):
    func: int

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

    def set_state(self) -> None:
        glViewport(self.x, self.y, self.width, self.height)

@dataclass(frozen=True)
class UniformBufferState(State):
    name: str
    binding: int



@dataclass(frozen=True)
class ShaderUniformState(State):
    program: ShaderProgram
    name: str
    group: Group

    sets_state: bool = True

    def set_state(self) -> None:
        self.program[self.name] = self.group.data[self.name]

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: State) -> bool:
        return False
