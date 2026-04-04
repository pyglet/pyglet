"""Configuration options for the Graphics Context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import UserConfig, SurfaceConfig
from .gl import OpenGLUserConfig, WebGLUserConfig
from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.window import Window


class Configs:
    opengl: OpenGLUserConfig = OpenGLUserConfig(opengl_api=GraphicsAPI.OPENGL)
    gl2: OpenGLUserConfig = OpenGLUserConfig(opengl_api=GraphicsAPI.OPENGL_2)
    gles2: OpenGLUserConfig = OpenGLUserConfig(opengl_api=GraphicsAPI.OPENGL_ES_2)
    gles3: OpenGLUserConfig = OpenGLUserConfig(opengl_api=GraphicsAPI.OPENGL_ES_3)
    webgl: WebGLUserConfig = WebGLUserConfig()
    # vulkan:TBD


def match_surface_config(config: UserConfig, surface: Window) -> SurfaceConfig | None:
    if isinstance(config, (OpenGLUserConfig, WebGLUserConfig)):
        from pyglet.config.gl import get_surface_config  # noqa: PLC0415
        return get_surface_config(config, surface)

    msg = f"Matching for '{config.__class__}' is not yet implemented."
    raise NotImplementedError(msg)
