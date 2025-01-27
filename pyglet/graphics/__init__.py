"""Low-level graphics rendering and abstractions.

This module provides efficient abstractions over OpenGL objects, such as
Shaders and Buffers. It also provides classes for highly performant batched
rendering and grouping.

See the :ref:`guide_graphics` for details on how to use this graphics API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence
from enum import Enum, auto

from pyglet.graphics.base import GeometryMode
from pyglet.graphics import api
from pyglet.graphics.draw import Group, ShaderGroup  # noqa: F401
from pyglet.graphics.api import Batch, get_default_shader, get_default_batch, global_backend, Shader, ShaderProgram

#
# def _load_backend_base(name: str):
#     if pyglet.options.backend == "opengl":
#         backend_module = importlib.import_module("pyglet.backend.gl.graphics")
#     else:
#         raise ValueError("Unsupported backend selected")
#
#     return getattr(backend_module, name)
#
#
# get_default_shader: Callable[[], ShaderProgram] = _load_backend_base("get_default_shader")


global_backend.post_init()
