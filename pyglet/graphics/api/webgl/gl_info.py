from __future__ import annotations
from pyglet.graphics.api.webgl.gl import GL_VENDOR, GL_RENDERER, GL_VERSION, GL_SHADING_LANGUAGE_VERSION
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl.webgl_js import WebGLRenderingContext


class GLInfo:
    """Information interface for a single GL context.

    A default instance is created automatically when the first OpenGL context
    is created.  You can use the module functions as a convenience for
    this default instance's methods.

    If you are using more than one context, you must call `set_active_context`
    when the context is active for this `GLInfo` instance.
    """
    extensions: set[str]
    vendor: str = ''
    renderer: str = ''
    version: str = '0.0'
    major_version: int = 0
    minor_version: int = 0
    opengl_api: str = 'gl'

    _have_context: bool = False

    # Whether the info has been queried yet. Can only be queried once it's made current.
    was_queried = False

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        self.extensions = set()

    def query(self, gl: WebGLRenderingContext) -> None:
        """Store information for the currently active context.

        Combines any information from the platform information.
        """
        self.vendor = gl.getParameter(GL_VENDOR)
        self.renderer = gl.getParameter(GL_RENDERER)
        self.version = gl.getParameter(GL_VERSION)
        self.language = gl.getParameter(GL_SHADING_LANGUAGE_VERSION)
        self.opengl_api = "webgl"

        self.major_version = 2 if "WebGL 2" in self.version else 1
        self.minor_version = 0
        self.extensions = set(gl.getSupportedExtensions())

        self.MAX_ARRAY_TEXTURE_LAYERS = gl.getParameter(gl.MAX_ARRAY_TEXTURE_LAYERS)
        """Value indicates the maximum number of layers allowed in a texture array"""

        self.MAX_TEXTURE_SIZE = gl.getParameter(gl.MAX_TEXTURE_SIZE)
        """The largest texture size available."""

        self.MAX_COLOR_ATTACHMENTS = gl.getParameter(gl.MAX_COLOR_ATTACHMENTS)
        """Get the maximum allowable framebuffer color attachments."""

        # gl.MAX_COLOR_TEXTURE_SAMPLES does not exist in WebGL context, but is defined as 0x910E in the spec.
        # WEBGL doesn't allow multisampled color textures, only multisampled renderbuffers.
        # Use MAX_SAMPLES instead?
        self.MAX_COLOR_TEXTURE_SAMPLES = gl.getParameter(gl.MAX_SAMPLES)
        """Maximum number of samples in a color multisample texture"""

        self.MAX_TEXTURE_IMAGE_UNITS = gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS)
        """Maximum number of texture units that can be used."""

        self.MAX_UNIFORM_BUFFER_BINDINGS = gl.getParameter(gl.MAX_UNIFORM_BUFFER_BINDINGS)


        self.was_queried = True

    def have_extension(self, extension: str) -> bool:
        """Determine if an OpenGL extension is available.

        Args:
            extension:
                The name of the extension to test for, including its ``GL_`` prefix.

        Returns:
            True if the extension is provided by the driver.
        """
        return extension in self.extensions

    def get_extensions(self) -> set[str]:
        """Get a set of available OpenGL extensions."""
        return self.extensions

    def get_version(self) -> tuple[int, int]:
        """Get the current major and minor version of OpenGL."""
        return self.major_version, self.minor_version

    def get_version_string(self) -> str:
        """Get the current OpenGL version string."""
        return self.version

    def have_version(self, major: int, minor: int = 0) -> bool:
        """Determine if a version of OpenGL is supported.

        Args:
            major:
                The major revision number (typically 1 or 2).
            minor:
                The minor revision number.

        Returns:
            ``True`` if the requested or a later version is supported.
        """
        if not self.major_version and not self.minor_version:
            return False

        return (self.major_version > major or
                (self.major_version == major and self.minor_version >= minor) or
                (self.major_version == major and self.minor_version == minor))

    def get_renderer(self) -> str:
        """Determine the renderer string of the OpenGL context."""
        return self.renderer

    def get_vendor(self) -> str:
        """Determine the vendor string of the OpenGL context."""
        return self.vendor

    def get_opengl_api(self) -> str:
        """Determine the OpenGL API version.

        Usually ``gl`` or ``gles``.
        """
        return self.opengl_api