from __future__ import annotations

from typing import Generator, Any, TYPE_CHECKING

import pyglet

from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.graphics.api.base import SurfaceContext


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

    #: States that are required to be active before this can be called. Used to help reduce redundant calls.
    parents: bool = False

    def generate_parent_states(self) -> Generator[State | None, None, None]:
        """Generate any additional states that are required before this state can be active.

        Dependents flag must be set to True for this to have any effect.
        """
        yield None

    def set_state(self, ctx: SurfaceContext) -> None:
        """Called when the state is set (enters scope)."""

    def unset_state(self, ctx: SurfaceContext) -> None:
        """Called when the state is unset (leaves scope)."""

    def resolve_state(self, *args: Any) -> None:
        """Resolve state during the draw phase.

        In some cases, a state may rely on something existing only during the draw phase. This allows an argument to be
        passed to the function to process the state being set.

        For example, in Vulkan, a descriptor set is not available during the Group creation, it only gets created
        when the draw list is being processed.
        """


def _expand_states_in_order(states: list[State]) -> list[State]:
    """Return all states expanded in dependency order (parents first)."""
    visited = set()
    ordered = []

    def dfs(state: State) -> None:
        if state in visited:
            return
        visited.add(state)

        if state.parents:
            for parent in state.generate_parent_states():
                dfs(parent)

        ordered.append(state)

    for s in states:
        dfs(s)

    return ordered


if pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2, GraphicsAPI.OPENGL_ES_3):
    from pyglet.graphics.api.gl import state as _backend_state
elif pyglet.options.backend == GraphicsAPI.WEBGL:
    from pyglet.graphics.api.webgl import state as _backend_state
elif pyglet.options.backend == GraphicsAPI.VULKAN:
    from pyglet.graphics.api.vulkan import state as _backend_state
else:
    msg = f"Unsupported backend: {pyglet.options.backend}"
    raise RuntimeError(msg)

TextureState: type[State] = _backend_state.TextureState
ShaderProgramState: type[State] = _backend_state.ShaderProgramState
BlendState: type[State] = _backend_state.BlendState
ShaderUniformState: type[State] = _backend_state.ShaderUniformState
UniformBufferState: type[State] = _backend_state.UniformBufferState
DepthBufferComparison: type[State] = _backend_state.DepthBufferComparison
ScissorState: type[State] = _backend_state.ScissorState
ViewportState: type[State] = _backend_state.ViewportState
