from __future__ import annotations
import pyglet
from pyglet.config import UserConfig, SurfaceConfig, OpenGLConfig


class GLSurfaceConfig(SurfaceConfig):
    config: OpenGLConfig


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
        return GLSurfaceConfig(surface, user_config, None)
    return None
