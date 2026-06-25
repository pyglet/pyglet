from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Any, TYPE_CHECKING, Protocol, runtime_checkable
from abc import ABC, abstractmethod

import pyglet

from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.window.camera.base import _CameraViewBase
    from pyglet.customtypes import ScissorProtocol
    from pyglet.graphics.draw import DrawContext
    from pyglet.window.camera import ViewportType


class State:
    """Base class for all states with optional scope methods."""
    #: Flag whether this state has a function to call when it comes into scope.
    sets_state: bool = False

    #: Flag whether this state has a function to call when it leaves scope.
    unsets_state: bool = False

    #: Flag whether this state needs resolution during the draw phase.
    resolves_state: bool = True

    #: Flag whether this state is to be used to calculate the group hash and comparison.
    group_hash: bool = True

    #: Flag for when this state belongs to a parental group, that the state should be re-applied
    #: to any child groups that do not have this state set.
    enforced_state: bool = False

    #: States that are required to be active before this can be called. Used to help reduce redundant calls.
    parents: bool = False

    def generate_parent_states(self) -> Generator[State | None, None, None]:
        """Generate any additional states that are required before this state can be active.

        Dependents flag must be set to True for this to have any effect.
        """
        yield None

    def set_state(self, ctx: DrawContext) -> None:
        """Called when the state is set (enters scope)."""

    def unset_state(self, ctx: DrawContext) -> None:
        """Called when the state is unset (leaves scope)."""

    def resolve_state(self, *args: Any) -> None:
        """Resolve state during the draw phase.

        In some cases, a state may rely on something existing only during the draw phase. This allows an argument to be
        passed to the function to process the state being set.

        For example, in Vulkan, a descriptor set is not available during the Group creation, it only gets created
        when the draw list is being processed.
        """

@runtime_checkable
class CameraScopeProtocol(Protocol):
    """Protocol for camera objects used by camera scope states."""
    view: _CameraViewBase

    @property
    def viewport(self) -> ViewportType:
        ...

    def begin(self, *, draw_context: DrawContext, commit: bool = True) -> None:
        ...

    def get_group_scissor_area(self) -> ScissorProtocol | None:
        ...


@runtime_checkable
class CameraScissorProviderProtocol(Protocol):
    """Protocol for camera/view objects that can provide a scissor object."""

    def get_group_scissor_area(self) -> ScissorProtocol | None:
        ...


@dataclass(frozen=True)
class CameraScopeState(State):
    """State wrapper that applies camera state at draw scope entry."""

    camera: CameraScopeProtocol
    sets_state: bool = True
    unsets_state: bool = True
    enforced_state: bool = True

    def set_state(self, ctx: DrawContext) -> None:
        ctx.camera_stack.append(self.camera)
        ctx.apply_camera_scope()

    def unset_state(self, ctx: DrawContext) -> None:
        if ctx.camera_stack:
            ctx.camera_stack.pop()
            ctx.apply_camera_scope(commit=False)


class _BaseViewportState(State, ABC):
    """State wrapper that applies viewport state at draw scope entry."""

    sets_state: bool = True
    unsets_state: bool = True

    @abstractmethod
    def apply_to_backend(self, ctx: DrawContext) -> None:
        """Apply the current viewport stack to the backend."""

    def set_state(self, ctx: DrawContext) -> None:
        ctx.viewport_stack.append(self)
        self.apply_to_backend(ctx)

    def unset_state(self, ctx: DrawContext) -> None:
        if ctx.viewport_stack:
            ctx.viewport_stack.pop()
        self.apply_to_backend(ctx)


class _BaseScissorState(State, ABC):
    """State wrapper that applies scissor state at draw scope entry."""

    sets_state: bool = True
    unsets_state: bool = True

    @abstractmethod
    def apply_to_backend(self, ctx: DrawContext) -> None:
        """Apply the current scissor stack to the backend."""

    def set_state(self, ctx: DrawContext) -> None:
        ctx.scissor_stack.append(self)
        self.apply_to_backend(ctx)

    def unset_state(self, ctx: DrawContext) -> None:
        if ctx.scissor_stack:
            ctx.scissor_stack.pop()
        self.apply_to_backend(ctx)


def _expand_states_in_order(states: tuple[State]) -> list[State]:
    """Return all states expanded in dependency order (parents first)."""
    visited = set()
    ordered = []

    def dfs(state: State | None) -> None:
        if state in visited or not state:
            return
        visited.add(state)

        if state.parents:
            for parent in state.generate_parent_states():
                dfs(parent)

        ordered.append(state)

    for s in states:
        dfs(s)

    return ordered


if pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3):
    from pyglet.graphics.api.gl import state as _backend_state
elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
    from pyglet.graphics.api.gl2 import state as _backend_state
elif pyglet.options.backend == GraphicsAPI.WEBGL:
    from pyglet.graphics.api.webgl import state as _backend_state
elif pyglet.options.backend == GraphicsAPI.VULKAN:
    from pyglet.graphics.api.vulkan import state as _backend_state
else:
    msg = f"Unsupported backend: {pyglet.options.backend}"
    raise RuntimeError(msg)

TextureState: type[State] = _backend_state.TextureState
MultiTextureSamplerState: type[State] = _backend_state.MultiTextureSamplerState
ShaderProgramState: type[State] = _backend_state.ShaderProgramState
BlendState: type[State] = _backend_state.BlendState
ShaderUniformState: type[State] = _backend_state.ShaderUniformState
UniformBufferState: type[State] = _backend_state.UniformBufferState
DepthBufferComparison: type[State] = _backend_state.DepthBufferComparison
ScissorState: type[State] = _backend_state.ScissorState
ViewportState: type[State] = _backend_state.ViewportState
