from __future__ import annotations

from pyglet.graphics.api.base import GraphicsConfig

from pyglet.graphics.api.base import VerifiedGraphicsConfig
from pyglet.graphics.api.webgl.context import OpenGLWindowContext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.window import Window
    from pyglet.graphics.api.webgl import WebGLBackend


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

    def create_context(self, opengl_backend: WebGLBackend, share: OpenGLWindowContext) -> OpenGLWindowContext:
        """Create a GL context that satisfies this configuration.

        Args:
            share:
                If not ``None``, a Context with which to share objects with.
        """
        return OpenGLWindowContext(opengl_backend, self._window, self._config, None)


class OpenGLConfig(GraphicsConfig):
    """An OpenGL Graphics configuration."""
    #: Specify the presence of a back-buffer for every color buffer.
    double_buffer: bool
    #: Specify the presence of separate left and right buffer sets.
    stereo: bool
    #: Total bits per sample per color buffer.
    buffer_size: int
    #: The number of auxiliary color buffers.
    aux_buffers: int
    #: The number of multisample buffers.
    sample_buffers: int
    #: The number of samples per pixel, or 0 if there are no multisample buffers.
    samples: int
    #: Bits per sample per buffer devoted to the red component.
    red_size: int
    #: Bits per sample per buffer devoted to the green component.
    green_size: int
    #: Bits per sample per buffer devoted to the blue component.
    blue_size: int
    #: Bits per sample per buffer devoted to the alpha component.
    alpha_size: int
    #: Bits per sample in the depth buffer.
    depth_size: int
    #: Bits per sample in the stencil buffer.
    stencil_size: int
    #: Bits per pixel devoted to the red component in the accumulation buffer.
    accum_red_size: int
    #: Bits per pixel devoted to the green component in the accumulation buffer.
    accum_green_size: int
    #: Bits per pixel devoted to the blue component in the accumulation buffer.
    accum_blue_size: int
    #: Bits per pixel devoted to the alpha component in the accumulation buffer.
    accum_alpha_size: int
    #: The OpenGL major version.
    major_version: int
    #: The OpenGL minor version.
    minor_version: int
    #: Whether to use forward compatibility mode.
    forward_compatible: bool
    #: The OpenGL API, such as "gl" or "gles".
    opengl_api: str = "gl"
    #: Debug mode.
    debug: bool

    def match(self, window: Window) -> OpenGLWindowConfig:
        return OpenGLWindowConfig(window, self)

    @property
    def finalized_config(self) -> OpenGLWindowConfig | None:
        return self._finalized_config

    def get_gl_attributes(self) -> list[tuple[str, bool | int | str]]:
        """Return a list of attributes set on this config.

        The attributes are returned as a list of tuples, containing
        the name and values. Any unset attributes will have a value
        of ``None``.
        """
        return [(name, getattr(self, name)) for name in self._attributes]
