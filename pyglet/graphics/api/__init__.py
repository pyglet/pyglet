from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import pyglet

from pyglet.enums import GraphicsAPI
from pyglet.graphics.api.base import ResourceManagement, NullBackend

if TYPE_CHECKING:
    from pyglet.graphics.api.base import GraphicsConfig
    from pyglet.graphics.draw import Batch
    from pyglet.graphics.shader import ShaderType, ShaderProgram

core = NullBackend()

resource_manager = ResourceManagement()


# Enforce WebGL if emscripten is detected.
# Create better fallback/choosing system later.
if pyglet.compat_platform == "emscripten":
    pyglet.options.backend = GraphicsAPI.WEBGL

if pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3):
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend

    core = OpenGLBackend(gl_api=pyglet.options.backend)

elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
    from pyglet.graphics.api.gl2.global_opengl import OpenGL2Backend

    core = OpenGL2Backend(gl_api=pyglet.options.backend)

elif pyglet.options.backend == GraphicsAPI.WEBGL:
    from pyglet.graphics.api.webgl import WebGLBackend

    core = WebGLBackend()

elif pyglet.options.backend == GraphicsAPI.VULKAN:
    from pyglet.graphics.api.vulkan.instance import VulkanGlobal
    core = VulkanGlobal()

else:
    raise Exception(f"Invalid rendering backend. Choose one of {[str(a) for a in GraphicsAPI]}.")


def get_config(**kwargs: float | str | None) -> GraphicsConfig:
    return core.get_config(**kwargs)


def get_default_configs() -> Sequence[GraphicsConfig]:
    return core.get_default_configs()


def have_version(*args: float) -> bool:
    return core.have_version(*args)


def have_extension(extension_name: str) -> bool:
    return core.have_extension(extension_name)


def get_cached_shader(name: str, *sources: tuple[str, ShaderType]) -> ShaderProgram:
    return core.get_cached_shader(name, *sources)


def get_default_batch() -> Batch:
    from pyglet.graphics.draw import get_default_batch as _get_default_batch

    return _get_default_batch()


def get_default_shader() -> ShaderProgram:
    from pyglet.graphics.shader import get_default_shader as _get_default_shader

    return _get_default_shader()
