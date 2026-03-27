from __future__ import annotations
from typing import TYPE_CHECKING

from pyglet.graphics.api.base import SurfaceInfo
from pyglet.graphics.api.webgl.gl import GL_VENDOR, GL_RENDERER, GL_VERSION, GL_SHADING_LANGUAGE_VERSION

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl.webgl_js import WebGLRenderingContext


class GLInfo(SurfaceInfo):
    """Information interface for a single GL context.

    A default instance is created automatically when the first OpenGL context
    is created.  You can use the module functions as a convenience for
    this default instance's methods.

    If you are using more than one context, you must call `set_active_context`
    when the context is active for this `GLInfo` instance.
    """
    def __init__(self) -> None:  # noqa: D107
        super().__init__()

    @staticmethod
    def _get_parameter(gl: WebGLRenderingContext, enum_name: str, default: int = 0) -> int:
        enum = getattr(gl, enum_name, None)
        if enum is None:
            return default

        value = gl.getParameter(enum)
        if value is None:
            return default

        return int(value)

    def query(self, gl: WebGLRenderingContext) -> None:
        """Store information for the currently active context.

        Combines any information from the platform information.
        """
        self.vendor = gl.getParameter(GL_VENDOR)
        self.renderer = gl.getParameter(GL_RENDERER)
        self.version = gl.getParameter(GL_VERSION)
        self.shading_language_version = gl.getParameter(GL_SHADING_LANGUAGE_VERSION)
        self.api = "webgl"

        self.major_version = 2 if "WebGL 2" in self.version else 1
        self.minor_version = 0
        self.extensions = set(gl.getSupportedExtensions() or [])

        self.MAX_ARRAY_TEXTURE_LAYERS = self._get_parameter(gl, "MAX_ARRAY_TEXTURE_LAYERS")
        """Value indicates the maximum number of layers allowed in a texture array"""

        self.MAX_TEXTURE_SIZE = self._get_parameter(gl, "MAX_TEXTURE_SIZE")
        """The largest texture size available."""

        self.MAX_COLOR_ATTACHMENTS = self._get_parameter(gl, "MAX_COLOR_ATTACHMENTS")
        """Get the maximum allowable framebuffer color attachments."""

        # gl.MAX_COLOR_TEXTURE_SAMPLES does not exist in WebGL context, but is defined as 0x910E in the spec.
        # WEBGL doesn't allow multisampled color textures, only multisampled renderbuffers.
        # Use MAX_SAMPLES instead?
        self.MAX_SAMPLES = self._get_parameter(gl, "MAX_SAMPLES")
        self.MAX_COLOR_TEXTURE_SAMPLES = self.MAX_SAMPLES
        """Maximum number of samples in a color multisample texture"""

        self.MAX_TEXTURE_IMAGE_UNITS = self._get_parameter(gl, "MAX_TEXTURE_IMAGE_UNITS")
        """Maximum number of texture units that can be used."""

        self.MAX_COMBINED_TEXTURE_IMAGE_UNITS = self._get_parameter(gl, "MAX_COMBINED_TEXTURE_IMAGE_UNITS")
        self.MAX_UNIFORM_BUFFER_BINDINGS = self._get_parameter(gl, "MAX_UNIFORM_BUFFER_BINDINGS")
        self.MAX_UNIFORM_BLOCK_SIZE = self._get_parameter(gl, "MAX_UNIFORM_BLOCK_SIZE")
        self.MAX_VERTEX_ATTRIBS = self._get_parameter(gl, "MAX_VERTEX_ATTRIBS")

        self.was_queried = True
