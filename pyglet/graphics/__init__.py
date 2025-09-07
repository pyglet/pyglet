"""Low-level graphics rendering and abstractions.

This module provides efficient abstractions over OpenGL objects, such as
Shaders and Buffers. It also provides classes for highly performant batched
rendering and grouping.

See the :ref:`guide_graphics` for details on how to use this graphics API.
"""
from __future__ import annotations


from pyglet.graphics.base import GeometryMode  # noqa: F401
from pyglet.graphics import api  # noqa: F401
from pyglet.graphics.draw import Group, ShaderGroup  # noqa: F401
from pyglet.graphics.api import Batch, get_default_shader, get_default_batch, core, Shader, ShaderProgram, ComputeShaderProgram  # noqa: F401
from pyglet.graphics.texture import Texture, TextureGrid, Texture3D, TextureDescriptor   # noqa: F401
from pyglet.graphics.atlas import TextureBin, TextureArrayBin, TextureAtlas   # noqa: F401
#
# def _load_backend_base(name: str):
#     if pyglet.options.backend == "opengl":
#         backend_module = importlib.import_module("pyglet.graphics.api.gl.graphics")
#     else:
#         raise ValueError("Unsupported backend selected")
#
#     return getattr(backend_module, name)
#
#
# get_default_shader: Callable[[], ShaderProgram] = _load_backend_base("get_default_shader")


core.post_init()
