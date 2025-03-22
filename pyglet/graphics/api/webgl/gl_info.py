from pyglet.graphics.api.webgl.gl import glGetParameter, GL_VENDOR, GL_RENDERER, GL_VERSION, _gl_context, glGetSupportedExtensions


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

        # A subset of OpenGL that is platform specific. (WGL, GLX)
        self.platform_info = None

    def query(self) -> None:
        """Store information for the currently active context.

        Combines any information from the platform information.
        """
        self.vendor = glGetParameter(GL_VENDOR)
        self.renderer = glGetParameter(GL_RENDERER)
        self.version = glGetParameter(GL_VERSION)
        self.language = glGetParameter(_gl_context.SHADING_LANGUAGE_VERSION)
        self.opengl_api = "webgl"

        self.major_version = 2 if "WebGL 2" in self.version else 1
        self.minor_version = 0
        self.extensions = glGetSupportedExtensions()


        if self.platform_info:
            self.extensions.update(set(self.platform_info.get_extensions()))

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