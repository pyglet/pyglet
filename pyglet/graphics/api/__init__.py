from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import pyglet
from pyglet.graphics.api.base import ResourceManagement

if TYPE_CHECKING:
    from pyglet.graphics.api.base import GraphicsConfig
    from pyglet.graphics.shader import ShaderType

global_backend = None

resource_manager = ResourceManagement()

if pyglet.options.backend == "opengl":
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend

    global_backend = OpenGLBackend()

    from pyglet.graphics.api.gl.draw import Batch
    from pyglet.graphics.api.gl.draw import get_default_shader, get_default_batch, get_default_blit_shader
    from pyglet.graphics.api.gl.shader import ShaderProgram, Shader, ComputeShaderProgram

elif pyglet.options.backend == "gl2":
    from pyglet.graphics.api.gl2.global_opengl import OpenGL2Backend

    global_backend = OpenGL2Backend()

    from pyglet.graphics.api.gl2.draw import Batch
    from pyglet.graphics.api.gl2.draw import get_default_shader, get_default_batch, get_default_blit_shader
    from pyglet.graphics.api.gl2.shader import ShaderProgram, Shader, ComputeShaderProgram

elif pyglet.options.backend == "gles2":
    from pyglet.graphics.api.gles2.global_opengl import OpenGLES2Backend

    global_backend = OpenGLES2Backend()

    from pyglet.graphics.api.gl2.draw import Batch
    from pyglet.graphics.api.gl2.draw import get_default_shader, get_default_batch, get_default_blit_shader
    from pyglet.graphics.api.gl2.shader import ShaderProgram, Shader, ComputeShaderProgram

elif pyglet.options.backend == "vulkan":
    from pyglet.graphics.api.vulkan.instance import VulkanGlobal
    global_backend = VulkanGlobal()

    from pyglet.graphics.api.vulkan.draw import Batch
    from pyglet.graphics.api.vulkan.draw import get_default_shader, get_default_batch, get_default_blit_shader
    from pyglet.graphics.api.vulkan.shader import ShaderProgram, Shader
else:
    raise Exception("Backend not set. Cannot utilize a graphics API.")


def get_config(**kwargs: float | str | None) -> GraphicsConfig:
    return global_backend.get_config(**kwargs)


def get_default_configs() -> Sequence[GraphicsConfig]:
    return global_backend.get_default_configs()


def have_version(*args: float) -> bool:
    return global_backend.have_version(*args)


def have_extension(extension_name: str) -> bool:
    return global_backend.have_extension(extension_name)


def get_cached_shader(name: str, *sources: tuple[str, ShaderType]) -> ShaderProgram:
    return global_backend.get_cached_shader(name, *sources)
