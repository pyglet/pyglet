from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import pyglet
from pyglet.graphics.api.base import ResourceManagement

if TYPE_CHECKING:
    from pyglet.graphics.api.base import GraphicsConfig
    from pyglet.graphics.shader import ShaderType

core = None

resource_manager = ResourceManagement()


# Enforce WebGL if emscripten is detected.
# Create better fallback/choosing system later.
if pyglet.compat_platform == "emscripten":
    pyglet.options.backend = "webgl"

if pyglet.options.backend in ("opengl", "gles3"):
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend

    core = OpenGLBackend("gles" if pyglet.options.backend == "gles3" else "gl")

    from pyglet.graphics.api.gl.draw import Batch
    from pyglet.graphics.api.gl.draw import get_default_shader, get_default_batch
    from pyglet.graphics.api.gl.shader import ShaderProgram, Shader, ComputeShaderProgram

elif pyglet.options.backend in ("gl2", "gles2"):
    from pyglet.graphics.api.gl2.global_opengl import OpenGL2Backend

    core = OpenGL2Backend("gles" if pyglet.options.backend == "gles2" else "gl")

    from pyglet.graphics.api.gl2.draw import Batch
    from pyglet.graphics.api.gl2.draw import get_default_shader, get_default_batch
    from pyglet.graphics.api.gl2.shader import ShaderProgram, Shader, ComputeShaderProgram

elif pyglet.options.backend == "webgl":
    from pyglet.graphics.api.webgl import WebGLBackend

    core = WebGLBackend()

    from pyglet.graphics.api.webgl.draw import Batch
    from pyglet.graphics.api.webgl.draw import get_default_shader, get_default_batch
    from pyglet.graphics.api.webgl.shader import ShaderProgram, Shader, ComputeShaderProgram

elif pyglet.options.backend == "vulkan":
    from pyglet.graphics.api.vulkan.instance import VulkanGlobal
    core = VulkanGlobal()

    from pyglet.graphics.api.vulkan.draw import Batch
    from pyglet.graphics.api.vulkan.draw import get_default_shader, get_default_batch
    from pyglet.graphics.api.vulkan.shader import ShaderProgram, Shader
else:
    raise Exception("Backend not set. Cannot utilize a graphics API.")


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
