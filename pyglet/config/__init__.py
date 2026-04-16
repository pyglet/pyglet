"""Configuration options for the Graphics Context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from .base import UserConfig, SurfaceConfig
from .gl import OpenGLUserConfig, WebGLUserConfig
from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.window import Window


class Config:
    """A container for backend specific user configuration."""
    __slots__ = 'opengl', 'gl2', 'gles2', 'gles3', 'webgl', 'vulkan'

    def __init__(self):
        self.opengl: OpenGLUserConfig = OpenGLUserConfig(api=GraphicsAPI.OPENGL)
        self.gl2: OpenGLUserConfig = OpenGLUserConfig(api=GraphicsAPI.OPENGL_2)
        self.gles2: OpenGLUserConfig = OpenGLUserConfig(api=GraphicsAPI.OPENGL_ES_2)
        self.gles3: OpenGLUserConfig = OpenGLUserConfig(api=GraphicsAPI.OPENGL_ES_3)
        self.webgl: WebGLUserConfig = WebGLUserConfig()
        # self.vulkan: TBD


def match_surface_config(config: UserConfig, surface: Window) -> SurfaceConfig | None:
    if isinstance(config, (OpenGLUserConfig, WebGLUserConfig)):
        from pyglet.config.gl import get_surface_config  # noqa: PLC0415
        return get_surface_config(config, surface)

    msg = f"Matching for '{config.__class__}' is not yet implemented."
    raise NotImplementedError(msg)
