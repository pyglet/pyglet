"""Information about version and extensions of current GL implementation.

Usage::

    if pyglet.graphics.api.have_extension('GL_NV_register_combiners'):
        # ...

"""
from __future__ import annotations

import re
import sys
import warnings
from ctypes import c_char_p, cast, c_int, c_float
from typing import TYPE_CHECKING

from pyglet.enums import PixelFormat
from pyglet.graphics.api.base import (
    PixelFormatPreferences,
    PixelTransferFeatures,
    SurfaceFeatures,
    SurfaceInfo,
)
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
        self.MAX_UNIFORM_BUFFER_OFFSET_ALIGNMENT = self.get_int(
            getattr(gl, "GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT", 0),
            default=1,
        )
        self.MAX_UNIFORM_BLOCK_SIZE = self.get_int(getattr(gl, "GL_MAX_UNIFORM_BLOCK_SIZE", 0))
        self.MAX_VERTEX_ATTRIBS = self.get_int(getattr(gl, "GL_MAX_VERTEX_ATTRIBS", 0))

        # NOTE: The version string requirements for gles is a lot stricter
        #       so using this to rely on detecting the API is not too unreasonable
        is_gles2 = "opengl es 2" in self.version.lower()
        is_gles3 = "opengl es 3" in self.version.lower()
        self.api = "gles2" if is_gles2 else "gles3" if is_gles3 else "opengl"

        self.major_version = self.get_int(gl.GL_MAJOR_VERSION)
        """Major version number of the OpenGL API supported by the current context."""

        self.minor_version = self.get_int(gl.GL_MINOR_VERSION)
        """Minor version number of the OpenGL API supported by the current context"""

        # With older GL versions, the above constants may not be supported.
        if not self.major_version:
            if match := re.search(r'[0-4]\.\d+', self.version):
                version_string = match.group()
                major, minor = map(int, version_string.split("."))
                self.major_version = major
                self.minor_version = minor
            else:
                warnings.warn(f"Unable to determine GL version from driver version string: {self.version}.")

        num_ext = self.get_int(gl.GL_NUM_EXTENSIONS)
        if num_ext == 0:
            # No extensions present, attempt finding via old extension value.
            ext_str = self.get_str(gl.GL_EXTENSIONS)
            if ext_str == "Unknown":
                warnings.warn("Unable to retrieve GL extension list. Driver may be missing or corrupt.")
            else:
                self.extensions = set(ext_str.split())
        else:
            extensions = (self.get_str_index(gl.GL_EXTENSIONS, i) for i in range(num_ext))
            self.extensions = set(extensions)

        if self.platform_info:
            self.extensions.update(set(self.platform_info.get_extensions(context)))

        self.update_features()
        self.was_queried = True

    def update_features(self) -> None:
        """Populate OpenGL and OpenGL ES feature support."""
        is_desktop_gl = self.api == "opengl"
        is_gles = self.api in ("gles2", "gles3")

        def desktop_at_least(major: int, minor: int = 0) -> bool:
            return is_desktop_gl and self.have_version(major, minor)

        def gles_at_least(major: int, minor: int = 0) -> bool:
            return is_gles and self.have_version(major, minor)

        self.features = SurfaceFeatures(
            compute_shaders=(
                desktop_at_least(4, 3)
                or gles_at_least(3, 1)
                or self.have_extension("GL_ARB_compute_shader")
            ),
            shader_storage_buffers=(
                desktop_at_least(4, 3)
                or gles_at_least(3, 1)
                or self.have_extension("GL_ARB_shader_storage_buffer_object")
            ),
            uniform_buffers=desktop_at_least(3, 1) or gles_at_least(3, 0),
            sync_objects=(
                desktop_at_least(3, 2)
                or gles_at_least(3, 0)
                or self.have_extension("GL_ARB_sync")
            ),
            geometry_shaders=(
                desktop_at_least(3, 2)
                or gles_at_least(3, 2)
                or self.have_extension("GL_ARB_geometry_shader4")
                or self.have_extension("GL_EXT_geometry_shader")
            ),
            tessellation_shaders=(
                desktop_at_least(4, 0)
                or gles_at_least(3, 2)
                or self.have_extension("GL_ARB_tessellation_shader")
                or self.have_extension("GL_OES_tessellation_shader")
            ),
            base_vertex=(
                desktop_at_least(3, 2)
                or gles_at_least(3, 2)
                or self.have_extension("GL_ARB_draw_elements_base_vertex")
                or self.have_extension("GL_OES_draw_elements_base_vertex")
            ),
            persistent_buffers=desktop_at_least(4, 4) or self.have_extension("GL_ARB_buffer_storage"),
            separate_shader_objects=(
                desktop_at_least(4, 1)
                or gles_at_least(3, 1)
                or self.have_extension("GL_ARB_separate_shader_objects")
                or self.have_extension("GL_EXT_separate_shader_objects")
            ),
            pixel_buffer_objects=(
                desktop_at_least(2, 1)
                or gles_at_least(3, 0)
                or self.have_extension("GL_ARB_pixel_buffer_object")
                or self.have_extension("GL_EXT_pixel_buffer_object")
                or self.have_extension("GL_NV_pixel_buffer_object")
            ),
            texture_storage=(
                desktop_at_least(4, 2)
                or gles_at_least(3, 0)
                or self.have_extension("GL_ARB_texture_storage")
            ),
        )

        bgra_upload = is_desktop_gl or any(
            self.have_extension(extension)
            for extension in (
                "GL_EXT_texture_format_BGRA8888",
                "GL_APPLE_texture_format_BGRA8888",
                "GL_IMG_texture_format_BGRA8888",
            )
        )
        self.pixel_transfer = PixelTransferFeatures(
            bgra_upload=bgra_upload,
            bgra_readback=is_desktop_gl or self.have_extension("GL_EXT_read_format_bgra"),
            unpack_row_length=(
                is_desktop_gl
                or gles_at_least(3, 0)
                or self.have_extension("GL_EXT_unpack_subimage")
            ),
            pack_row_length=(
                is_desktop_gl
                or gles_at_least(3, 0)
                or self.have_extension("GL_NV_pack_subimage")
            ),
            direct_texture_readback=is_desktop_gl,
        )

        prefer_bgra = sys.platform == "win32" and bgra_upload
        self.pixel_format_preferences = PixelFormatPreferences(
            preferred_decode_format=PixelFormat.BGRA8 if prefer_bgra else PixelFormat.RGBA8,
            readback_format=(
                PixelFormat.BGRA8 if sys.platform == "win32" and is_desktop_gl else PixelFormat.RGBA8
            ),
        )
        self._apply_image_decode_policy()

    def get_int(self, enum: int, default: int = 0) -> int:
        try:
            value = c_int()
            self.context.glGetIntegerv(enum, value)
            return value.value
        except GLException:
            return default

    def get_float(self, enum: int, default: float = 0.0) -> float:
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
