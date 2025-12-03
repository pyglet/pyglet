from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet

if TYPE_CHECKING:
    from pyglet.image import ImageData


def get_screenshot() -> ImageData:
    """Read the pixel data from the default color buffer into ImageData.

    This provides a simplistic screenshot of the default frame buffer.

    This may be inaccurate if you utilize multiple frame buffers in your program.

    .. versionadded:: 3.0
    """
    raise NotImplementedError


if pyglet.options.backend in ("opengl", "gles3", "gl2", "gles2"):
    from pyglet.graphics.api.gl.framebuffer import Framebuffer, Renderbuffer
elif pyglet.options.backend == "webgl":
    from pyglet.graphics.api.webgl.framebuffer import Framebuffer, Renderbuffer  # noqa: F401
