"""Information about version and extensions of current GL implementation.

Usage::

    if pyglet.graphics.api.have_extension('GL_NV_register_combiners'):
        # ...

"""
from __future__ import annotations

from ctypes import c_char_p, cast, c_int, c_float
from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl.lib import GLException

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.win32.wgl_info import WGLInfo
    from pyglet.graphics.api.gl.xlib.glx_info import GLXInfo


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

    was_queried = False

    platform_info: GLXInfo | WGLInfo | None

    def __init__(self, platform_info: GLXInfo | WGLInfo | None) -> None:
        """Store information for the currently active context.

        Combines any information from the platform information.
        """
        super().__init__()
        self.extensions = set()

        # A subset of OpenGL that is platform specific. (WGL, GLX)
        self.platform_info = platform_info

    def query(self, context) -> None:
        self.context = context
        self.vendor = self.get_str(gl.GL_VENDOR)
        """The vendor string. For example 'NVIDIA Corporation'"""

        self.renderer = self.get_str(gl.GL_RENDERER)
        """The graphics renderer. For example "NVIDIA GeForce RTX 2080 SUPER/PCIe/SSE2"""

        self.version = self.get_str(gl.GL_VERSION)

        self.MAX_ARRAY_TEXTURE_LAYERS = self.get_int(gl.GL_MAX_ARRAY_TEXTURE_LAYERS)
        """Value indicates the maximum number of layers allowed in a texture array"""

        self.MAX_TEXTURE_SIZE = self.get_int(gl.GL_MAX_TEXTURE_SIZE)
        """The largest texture size available."""

        self.MAX_COLOR_ATTACHMENTS = self.get_int(gl.GL_MAX_COLOR_ATTACHMENTS)
        """Get the maximum allowable framebuffer color attachments."""

        self.MAX_COLOR_TEXTURE_SAMPLES = self.get_int(gl.GL_MAX_COLOR_TEXTURE_SAMPLES)
        """Maximum number of samples in a color multisample texture"""

        self.MAX_TEXTURE_IMAGE_UNITS = self.get_int(gl.GL_MAX_TEXTURE_IMAGE_UNITS)
        """Maximum number of texture units that can be used."""

        self.MAX_UNIFORM_BUFFER_BINDINGS = self.get_int(gl.GL_MAX_UNIFORM_BUFFER_BINDINGS)

        # NOTE: The version string requirements for gles is a lot stricter
        #       so using this to rely on detecting the API is not too unreasonable
        self.opengl_api = "gles" if "opengl es" in self.version.lower() else "gl"

        try:
            self.major_version = self.get_int(gl.GL_MAJOR_VERSION)
            """Major version number of the OpenGL API supported by the current context."""

            self.minor_version = self.get_int(gl.GL_MINOR_VERSION)
            """Minor version number of the OpenGL API supported by the current context"""

            num_ext = self.get_int(gl.GL_NUM_EXTENSIONS)
            extensions = (self.get_str_index(gl.GL_EXTENSIONS, i) for i in range(num_ext))
            self.extensions = set(extensions)
        except GLException:
            pass  # GL3 is likely not available

        if self.platform_info:
            self.extensions.update(set(self.platform_info.get_extensions(context)))

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

    def get_int(self, enum: int, default: int=0) -> int | tuple[int]:
        try:
            value = c_int()
            self.context.glGetIntegerv(enum, value)
            return value.value
        except GLException:
            return default

    def get_float(self, enum: int, default=0.0) -> float:
        try:
            value = c_float()
            self.context.glGetFloatv(enum, value)
            return value.value
        except GLException:
            return default

    def get_str(self, enum: int) -> str:
        try:
            return cast(self.context.glGetString(enum), c_char_p).value.decode()
        except GLException:
            return "Unknown"

    def get_str_index(self, enum: int, index: int) -> str:
        try:
            return cast(self.context.glGetStringi(enum, index), c_char_p).value.decode()
        except GLException:
            return "Unknown"
