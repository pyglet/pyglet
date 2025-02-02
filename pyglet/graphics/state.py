from __future__ import annotations

from typing import Generator, Any

import pyglet


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
    dependents: bool = False

    def generate_dependent_states(self) -> Generator[State, None, None]:
        """Generate any additional states that are required before this state can be active.

        Dependents flag must be set to True for this to have any effect.
        """
        yield

    def set_state(self) -> None:
        """Called when the state is set (enters scope)."""

    def unset_state(self) -> None:
        """Called when the state is unset (leaves scope)."""

    def resolve_state(self, *args: Any) -> None:
        """Resolve state during the draw phase.

        In some cases, a state may rely on something existing only during the draw phase. This allows an argument to be
        passed to the function to process the state being set.

        For example, in Vulkan, a descriptor set is not available during the Group creation, it only gets created
        when the draw list is being processed.
        """

if "gl" in pyglet.options.backend:
    from pyglet.graphics.api.gl.state import (TextureState, ShaderProgramState, BlendState, # noqa: F401
                                              ShaderUniformState,
                                              UniformBufferState, DepthBufferComparison, ScissorState)
elif pyglet.options.backend == "vulkan":
    from pyglet.graphics.api.vulkan.state import *
