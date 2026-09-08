"""Configuration options for the Graphics Context."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from pyglet.enums import GraphicsAPI

from .base import SurfaceConfig, UserConfig  # noqa: TC001
from .gl import OpenGLUserConfig, WebGLUserConfig

if TYPE_CHECKING:
    from pyglet.window import Window


class Config:
    """A container for backend specific user configuration."""
    opengl: OpenGLUserConfig
    gl2: OpenGLUserConfig
    gles2: OpenGLUserConfig
    gles3: OpenGLUserConfig
    webgl: WebGLUserConfig

    __slots__ = 'gl2', 'gles2', 'gles3', 'opengl', 'vulkan', 'webgl'

    def __init__(self):
        self.opengl: OpenGLUserConfig = OpenGLUserConfig(major_version=3, minor_version=3, api=GraphicsAPI.OPENGL)
        self.gl2: OpenGLUserConfig = OpenGLUserConfig(major_version=2, minor_version=0, api=GraphicsAPI.OPENGL_2)
        self.gles2: OpenGLUserConfig = OpenGLUserConfig(major_version=2, minor_version=0, api=GraphicsAPI.OPENGL_ES_2)
        self.gles3: OpenGLUserConfig = OpenGLUserConfig(major_version=3, minor_version=2, api=GraphicsAPI.OPENGL_ES_3)
        self.webgl: WebGLUserConfig = WebGLUserConfig()
        # self.vulkan: TBD


def match_surface_config(config: UserConfig, surface: Window) -> SurfaceConfig | None:
    if isinstance(config, (OpenGLUserConfig, WebGLUserConfig)):
        from pyglet.config.gl import get_surface_config  # noqa: PLC0415
        return get_surface_config(config, surface)

    msg = f"Matching for '{config.__class__}' is not yet implemented."
    raise NotImplementedError(msg)
