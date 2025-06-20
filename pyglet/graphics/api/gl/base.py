from __future__ import annotations

import abc
from enum import Enum
from typing import TYPE_CHECKING

from pyglet.graphics.api.base import GraphicsConfig, VerifiedGraphicsConfig

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.context import OpenGLSurfaceContext
    from pyglet.window import Window
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend


class OpenGLAPI(Enum):
    """The OpenGL API backend to use."""
    OPENGL = 1
    OPENGL_ES = 2


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
    #: If the framebuffer should be transparent.
    transparent_framebuffer: bool

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

    # def create_context(self, window: Window, share: Context | None) -> Context:
    #     """Create a GL context that satisifies this configuration.
    #
    #     Args:
    #         share:
    #             If not ``None``, a context with which to share objects with.
    #     """
    #     if not self.finalized_config:
    #         msg = "This config has not finalized the available attributes."
    #         raise gl.ConfigException(msg)

    #def __repr__(self) -> str:
    #    return f"{self.__class__.__name__}({self.get_gl_attributes()})"


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

    @abc.abstractmethod
    def create_context(self, opengl_backend: OpenGLBackend, share: OpenGLSurfaceContext) -> OpenGLSurfaceContext:
        """Create a GL context that satisfies this configuration.

        Args:
            share:
                If not ``None``, a Context with which to share objects with.
        """


class ObjectSpace:
    """A container to store shared objects that are to be removed."""

    def __init__(self) -> None:
        """Initialize the context object space."""
        # Objects scheduled for deletion the next time this object space is active.
        self.doomed_textures = []
        self.doomed_buffers = []
        self.doomed_shader_programs = []
        self.doomed_shaders = []
        self.doomed_renderbuffers = []


class ContextException(Exception):
    pass


class ConfigException(Exception):
    pass


