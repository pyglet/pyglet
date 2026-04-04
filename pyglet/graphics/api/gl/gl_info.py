"""Information about version and extensions of current GL implementation.

Usage::

    if pyglet.graphics.api.have_extension('GL_NV_register_combiners'):
        # ...

"""
from __future__ import annotations

from ctypes import c_char_p, cast, c_int, c_float
from typing import TYPE_CHECKING

from pyglet.graphics.api.base import SurfaceInfo
from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl.lib import GLException

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.context import OpenGLSurfaceContext
    from pyglet.graphics.api.gl.win32.wgl_info import WGLInfo
    from pyglet.graphics.api.gl.xlib.glx_info import GLXInfo


class GLInfo(SurfaceInfo):
    """Information interface for a single GL context.

    A default instance is created automatically when the first OpenGL context
    is created.  You can use the module functions as a convenience for
    this default instance's methods.

    If you are using more than one context, you must call `set_active_context`
    when the context is active for this `GLInfo` instance.
    """
    platform_info: GLXInfo | WGLInfo | None
    context: OpenGLSurfaceContext

    def __init__(self, platform_info: GLXInfo | WGLInfo | None) -> None:
        """Store information for the currently active context.

        Combines any information from the platform information.
        """
        super().__init__()
        # A subset of OpenGL that is platform specific. (WGL, GLX)
        self.platform_info = platform_info

    def query(self, context: OpenGLSurfaceContext) -> None:
        self.context = context
        self.vendor = self.get_str(gl.GL_VENDOR)
        """The vendor string. For example 'NVIDIA Corporation'"""

        self.renderer = self.get_str(gl.GL_RENDERER)
        """The graphics renderer. For example "NVIDIA GeForce RTX 2080 SUPER/PCIe/SSE2"""

        self.version = self.get_str(gl.GL_VERSION)
        self.shading_language_version = self.get_str(gl.GL_SHADING_LANGUAGE_VERSION)

        self.MAX_ARRAY_TEXTURE_LAYERS = self.get_int(gl.GL_MAX_ARRAY_TEXTURE_LAYERS)
        """Value indicates the maximum number of layers allowed in a texture array"""

        self.MAX_TEXTURE_SIZE = self.get_int(gl.GL_MAX_TEXTURE_SIZE)
        """The largest texture size available."""

        self.MAX_COLOR_ATTACHMENTS = self.get_int(gl.GL_MAX_COLOR_ATTACHMENTS)
        """Get the maximum allowable framebuffer color attachments."""

        self.MAX_SAMPLES = self.get_int(gl.GL_MAX_SAMPLES)

        self.MAX_COLOR_TEXTURE_SAMPLES = self.get_int(gl.GL_MAX_COLOR_TEXTURE_SAMPLES,
                                                      default=self.MAX_SAMPLES)
        """Maximum number of samples in a color multisample texture"""

        self.MAX_TEXTURE_IMAGE_UNITS = self.get_int(gl.GL_MAX_TEXTURE_IMAGE_UNITS)
        """Maximum number of texture units that can be used."""

        self.MAX_COMBINED_TEXTURE_IMAGE_UNITS = self.get_int(gl.GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS,
                                                             default=gl.GL_MAX_TEXTURE_IMAGE_UNITS)

        self.MAX_UNIFORM_BUFFER_BINDINGS = self.get_int(getattr(gl, "GL_MAX_UNIFORM_BUFFER_BINDINGS", 0))
        self.MAX_UNIFORM_BLOCK_SIZE = self.get_int(getattr(gl, "GL_MAX_UNIFORM_BLOCK_SIZE", 0))
        self.MAX_VERTEX_ATTRIBS = self.get_int(getattr(gl, "GL_MAX_VERTEX_ATTRIBS", 0))

        # NOTE: The version string requirements for gles is a lot stricter
        #       so using this to rely on detecting the API is not too unreasonable
        is_gles2 = "opengl es 2" in self.version.lower()
        is_gles3 = "opengl es 3" in self.version.lower()
        self.opengl_api = "gles2" if is_gles2 else "gles3" if is_gles3 else "opengl"

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

    def get_int(self, enum: int, default: int = 0) -> int:
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
            value = cast(self.context.glGetString(enum), c_char_p).value
            return value.decode() if value else "Unknown"
        except GLException:
            return "Unknown"

    def get_str_index(self, enum: int, index: int) -> str:
        try:
            value = cast(self.context.glGetStringi(enum, index), c_char_p).value
            return value.decode() if value else "Unknown"
        except GLException:
            return "Unknown"
