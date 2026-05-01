"""Low-level graphics rendering and abstractions.

This module provides efficient abstractions over OpenGL objects, such as
Shaders and Buffers. It also provides classes for highly performant batched
rendering and grouping.

See the :ref:`guide_graphics` for details on how to use this graphics API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet


class UnsupportedBackendError(Exception):
    """Raised when a graphics feature is unavailable on the active backend."""

    def __init__(self, functionality: str, backend: GraphicsAPI | None = None) -> None:  # noqa: D107
        super().__init__(f"{functionality} is unsupported on backend '{backend or pyglet.options.backend}'.")
        self.functionality = functionality
        self.backend = backend


if TYPE_CHECKING:
    from pyglet.enums import GraphicsAPI
    from pyglet.graphics import api  # noqa: F401
    from pyglet.graphics.draw import Group, ShaderGroup, Batch  # noqa: F401
    from pyglet.graphics.shader import Shader, ShaderProgram, ComputeShaderProgram, TransformFeedbackShaderProgram  # noqa: F401
    from pyglet.graphics.state import State  # noqa: F401
    from pyglet.graphics.shader import get_default_shader  # noqa: F401
    from pyglet.graphics.draw import get_default_batch  # noqa: F401
    from pyglet.graphics.texture import Texture, TextureGrid, Texture3D, TextureArray  # noqa: F401
    from pyglet.graphics.atlas import TextureBin, TextureArrayBin, TextureAtlas  # noqa: F401
    from pyglet.graphics.framebuffer import Framebuffer, Renderbuffer  # noqa: F401
else:
    from pyglet.graphics import api  # noqa: F401
    from pyglet.graphics.draw import Group, ShaderGroup, Batch, get_default_batch  # noqa: F401
    from pyglet.graphics.shader import (  # noqa: F401
        Shader,
        ShaderProgram,
        ComputeShaderProgram,
        TransformFeedbackShaderProgram,
        get_default_shader,
    )
    from pyglet.graphics.state import State  # noqa: F401
    from pyglet.graphics.api import core  # noqa: F401
    from pyglet.graphics.texture import Texture, TextureGrid, Texture3D, TextureArray  # noqa: F401
    from pyglet.graphics.atlas import TextureBin, TextureArrayBin, TextureAtlas  # noqa: F401
    from pyglet.graphics.framebuffer import Framebuffer, Renderbuffer  # noqa: F401
