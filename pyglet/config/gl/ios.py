"""OpenGL ES surface configuration for UIKit windows."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.config.gl import GLSurfaceConfig
from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.config import OpenGLUserConfig
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
    from pyglet.graphics.api.gl.ios.context import IOSContext
    from pyglet.window.apple.ios import IOSWindow


def match(config: OpenGLUserConfig, window: IOSWindow) -> IOSGLSurfaceConfig | None:
    # iOS only supports GLES2 or 3.
    if config.api not in (GraphicsAPI.OPENGL_ES_2, GraphicsAPI.OPENGL_ES_3):
        return None
    version = 3 if config.api == GraphicsAPI.OPENGL_ES_3 else 2
    if (config.major_version or version, config.minor_version or 0) > (version, 0):
        return None
    if config.stereo or config.aux_buffers or config.sample_buffers or config.samples:
        return None
    limits = {'red_size': 8, 'green_size': 8, 'blue_size': 8, 'alpha_size': 8,
              'buffer_size': 32, 'depth_size': 24, 'stencil_size': 8,
              'accum_red_size': 0, 'accum_green_size': 0, 'accum_blue_size': 0, 'accum_alpha_size': 0}
    if any(getattr(config, name) is not None and not 0 <= getattr(config, name) <= limit
           for name, limit in limits.items()):
        return None
    return IOSGLSurfaceConfig(window, config)


class IOSGLSurfaceConfig(GLSurfaceConfig['IOSWindow']):

    def __init__(self, window: IOSWindow, config: OpenGLUserConfig) -> None:
        super().__init__(window, config, handle=None)
        self.double_buffer = True
        self.red_size = self.green_size = self.blue_size = self.alpha_size = 8
        self.buffer_size = 32
        depth = 16 if config.depth_size is None else config.depth_size
        self.depth_size = 24 if depth > 16 or (depth and config.stencil_size) else 16 if depth else 0
        self.stencil_size = 8 if config.stencil_size else 0
        self.sample_buffers = self.samples = 0
        self.stereo = self.aux_buffers = 0
        self.major_version = 3 if config.api == GraphicsAPI.OPENGL_ES_3 else 2
        self.minor_version = 0

    def create_context(self, opengl_backend: OpenGLBackend, share: IOSContext | None) -> IOSContext:
        from pyglet.graphics.api.gl.ios.context import IOSContext  # noqa: PLC0415

        return IOSContext(opengl_backend, self._window, self, share)

    def apply_format(self) -> None:
        return None
