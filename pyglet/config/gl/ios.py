"""OpenGL ES surface configuration for UIKit windows."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.config.gl import GLSurfaceConfig
from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.config import OpenGLUserConfig
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
    from pyglet.graphics.api.gl.ios.context import IOSContext
    from pyglet.window.ios import IOSWindow


def match(config: OpenGLUserConfig, window: IOSWindow) -> IOSGLSurfaceConfig | None:
    # iOS only supports GLES2 or 3.
    if config.api not in (GraphicsAPI.OPENGL_ES_2, GraphicsAPI.OPENGL_ES_3):
        return None
    if config.api == GraphicsAPI.OPENGL_ES_3 and (config.major_version or 3) > 3:
        return None
    return IOSGLSurfaceConfig(window, config)


class IOSGLSurfaceConfig(GLSurfaceConfig):

    def __init__(self, window: IOSWindow, config: OpenGLUserConfig) -> None:
        super().__init__(window, config, handle=None)
        self.double_buffer = True
        self.red_size = self.green_size = self.blue_size = self.alpha_size = 8
        self.buffer_size = 32
        self.depth_size = config.depth_size or 16
        self.stencil_size = config.stencil_size or 0
        self.sample_buffers = self.samples = 0
        self.stereo = self.aux_buffers = 0
        self.major_version = config.major_version or (3 if config.api == GraphicsAPI.OPENGL_ES_3 else 2)
        self.minor_version = config.minor_version or 0

    def create_context(self, opengl_backend: OpenGLBackend, share: IOSContext | None) -> IOSContext:
        from pyglet.graphics.api.gl.ios.context import IOSContext  # noqa: PLC0415

        return IOSContext(opengl_backend, self._window, self, share)

    def apply_format(self) -> None:
        return None
