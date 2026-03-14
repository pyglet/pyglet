"""Configuration options for the Graphics Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from pyglet.window import Window


class SurfaceConfig:
    """Surface configuration information returned by a platform.

    This describes the information a desired surface or window can support.
    """
    def __init__(self, window: Window, config: UserConfig, handle: Any) -> None:
        """A config representing the capabilities of a specific surface.

        This is returned by the platform on a specific window and is not meant to be created by users.

        Args:
            window:
                The current window or display.
            config:
                The requested user configuration.
            handle:
                A handle to the underlying configuration unique to each platform.
        """
        self._window = window
        self.config = config
        self.handle = handle

    @property
    def attributes(self) -> dict[str, Any]:
        """The public attributes of this configuration."""
        return {attrib: value for attrib, value in self.__dict__.items() if attrib[0] != '_'}

    @property
    def is_finalized(self) -> bool:
        return True


class UserConfig:
    """User configuration information."""


# Platform Specific Configurations

@dataclass
class OpenGLConfig(UserConfig):
    """An OpenGL Graphics configuration."""
    #: Specify the presence of a back-buffer for every color buffer.
    double_buffer: bool | None = None
    #: Specify the presence of separate left and right buffer sets.
    stereo: bool | None = None
    #: Total bits per sample per color buffer.
    buffer_size: int | None = None
    #: The number of auxiliary color buffers.
    aux_buffers: int | None = None
    #: The number of multisample buffers.
    sample_buffers: int | None = None
    #: The number of samples per pixel, or 0 if there are no multisample buffers.
    samples: int | None = None
    #: Bits per sample per buffer devoted to the red component.
    red_size: int | None = None
    #: Bits per sample per buffer devoted to the green component.
    green_size: int | None = None
    #: Bits per sample per buffer devoted to the blue component.
    blue_size: int | None = None
    #: Bits per sample per buffer devoted to the alpha component.
    alpha_size: int | None = None
    #: Bits per sample in the depth buffer.
    depth_size: int | None = None
    #: Bits per sample in the stencil buffer.
    stencil_size: int | None = None
    #: Bits per pixel devoted to the red component in the accumulation buffer. Deprecated.
    accum_red_size: int | None = None
    #: Bits per pixel devoted to the green component in the accumulation buffer. Deprecated.
    accum_green_size: int | None = None
    #: Bits per pixel devoted to the blue component in the accumulation buffer. Deprecated.
    accum_blue_size: int | None = None
    #: Bits per pixel devoted to the alpha component in the accumulation buffer. Deprecated.
    accum_alpha_size: int | None = None
    #: The OpenGL major version.
    major_version: int | None = None
    #: The OpenGL minor version.
    minor_version: int | None = None
    #: Whether to use forward compatibility mode.
    forward_compatible: bool | None = None
    #: Debug mode.
    debug: bool | None = None
    #: If the framebuffer should be transparent.
    transparent_framebuffer: bool | None = None

    opengl_api: str | None = "gl"

    @property
    def is_finalized(self) -> bool:
        return False


@dataclass
class WebGLConfig(UserConfig):
    """A WebGL Graphics configuration."""
    #: Whether the drawing buffer has an alpha channel (pyglet defaults to False).
    alpha: bool = False
    #: Whether the drawing buffer has a depth buffer (default True).
    depth: bool | None = None
    #: Whether the drawing buffer has a stencil buffer (default False).
    stencil: bool | None = None
    #: Whether antialiasing is enabled (default True).
    antialias: bool | None = None
    #: Whether color values are pre-multiplied by alpha (default True).
    premultipliedAlpha: bool | None = None
    #: Whether the drawing buffer is preserved after rendering (default False).
    preserveDrawingBuffer: bool | None = None
    #: Whether context creation fails if performance is low (default False).
    failIfMajorPerformanceCaveat: bool | None = None
    #: Hints GPU preference: "default", "low-power", or "high-performance" (default "default").
    powerPreference: str | None = None
    #: Hints to reduce latency by desynchronizing canvas painting (default False).
    desynchronized: bool | None = None

    @property
    def opengl_api(self):
        return "webgl"

    @property
    def is_finalized(self) -> bool:
        return False


def match_surface_config(config: UserConfig, surface: Window) -> SurfaceConfig | None:
    if isinstance(config, (OpenGLConfig, WebGLConfig)):
        from pyglet.config.gl import get_surface_config  # noqa: PLC0415
        return get_surface_config(config, surface)
    return None
