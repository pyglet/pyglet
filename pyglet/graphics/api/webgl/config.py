from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.graphics.api.base import VerifiedGraphicsConfig
from pyglet.graphics.api.webgl.context import OpenGLSurfaceContext

if TYPE_CHECKING:
    from pyglet.config import OpenGLConfig
    from pyglet.graphics.api.webgl import WebGLBackend
    from pyglet.window import Window


class OpenGLWindowConfig(VerifiedGraphicsConfig):
    """An OpenGL configuration for a particular display.

    Use ``Config.match`` to obtain an instance of this class.

    .. versionadded:: 1.2
    """

    def __init__(self, window: Window, base_config: OpenGLConfig) -> None:
        super().__init__(window, base_config)
        self.major_version = base_config.major_version
        self.minor_version = base_config.minor_version
        self.forward_compatible = base_config.forward_compatible
        self.opengl_api = base_config.opengl_api or base_config.opengl_api
        self.debug = base_config.debug

    def create_context(self, opengl_backend: WebGLBackend, share: OpenGLSurfaceContext) -> OpenGLSurfaceContext:
        """Create a GL context that satisfies this configuration.

        Args:
            share:
                If not ``None``, a Context with which to share objects with.
        """
        return OpenGLSurfaceContext(opengl_backend, self._window, self._config, None)

