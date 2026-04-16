from __future__ import annotations

from dataclasses import dataclass

import pyglet

from pyglet.enums import GraphicsAPI
from pyglet.config.base import UserConfig, SurfaceConfig


class GLSurfaceConfig(SurfaceConfig):
    config: OpenGLUserConfig


# Platform Specific Configurations

@dataclass
class OpenGLUserConfig(UserConfig):
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
    #: Which rendering API is being used (GL, ES, etc.).
    api: GraphicsAPI = GraphicsAPI.OPENGL

    @property
    def is_finalized(self) -> bool:
        return False


@dataclass
class WebGLUserConfig(UserConfig):
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
    def api(self):
        return GraphicsAPI.WEBGL

    @property
    def is_finalized(self) -> bool:
        return False


def get_surface_config(user_config: UserConfig, surface: pyglet.window.Window) -> SurfaceConfig | None:

    if pyglet.options.headless or pyglet.options.wayland:
        from pyglet.config.gl.egl import match

        return match(user_config, surface)

    if pyglet.compat_platform == "win32":
        from pyglet.config.gl.windows import match  # noqa: PLC0415

        return match(user_config, surface)

    if pyglet.compat_platform.startswith("linux"):
        from pyglet.config.gl.x11 import match  # noqa: PLC0415

        return match(user_config, surface)

    if pyglet.compat_platform == "darwin":
        from pyglet.config.gl.macos import match  # noqa: PLC0415

        return match(user_config, surface)

    if pyglet.compat_platform == "emscripten":
        from pyglet.config.gl.webgl import match  # noqa: PLC0415

        return match(user_config, surface)

    return None
