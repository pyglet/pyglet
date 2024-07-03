"""Information about version and extensions of current GL implementation.

Usage::

    from pyglet.gl import gl_info

    if gl_info.have_extension('GL_NV_register_combiners'):
        # ...

If you are using more than one context, you can set up a separate GLInfo
object for each context.  Call `set_active_context` after switching to the
context::

    from pyglet.gl.gl_info import GLInfo

    info = GLInfo()
    info.set_active_context()

    if info.have_version(4, 5):
        # ...

"""
from __future__ import annotations

import warnings
from ctypes import c_char_p, cast

from pyglet.gl.gl import GL_EXTENSIONS, GL_MAJOR_VERSION, GL_MINOR_VERSION, GL_RENDERER, GL_VENDOR, GL_VERSION, GLint
from pyglet.gl.lib import GLException
from pyglet.util import asstr


def _get_number(parameter: int) -> int:
    from pyglet.gl.gl import glGetIntegerv
    number = GLint()
    glGetIntegerv(parameter, number)
    return number.value


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
    _have_info = False

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        self.extensions = set()

    def set_active_context(self) -> None:
        """Store information for the currently active context.

        This method is called automatically for the default context.
        """
        self._have_context = True

        if not self._have_info:

            from pyglet.gl.gl import GL_NUM_EXTENSIONS, glGetString, glGetStringi

            self.vendor = asstr(cast(glGetString(GL_VENDOR), c_char_p).value)
            self.renderer = asstr(cast(glGetString(GL_RENDERER), c_char_p).value)
            self.version = asstr(cast(glGetString(GL_VERSION), c_char_p).value)
            # NOTE: The version string requirements for gles is a lot stricter
            #       so using this to rely on detecting the API is not too unreasonable
            self.opengl_api = "gles" if "opengl es" in self.version.lower() else "gl"

            try:
                self.major_version = _get_number(GL_MAJOR_VERSION)
                self.minor_version = _get_number(GL_MINOR_VERSION)
                num_ext = _get_number(GL_NUM_EXTENSIONS)
                self.extensions = (asstr(cast(glGetStringi(GL_EXTENSIONS, i), c_char_p).value) for i in range(num_ext))
                self.extensions = set(self.extensions)
            except GLException:
                pass  # GL3 is likely not available

            self._have_info = True

    def remove_active_context(self) -> None:
        self._have_context = False
        self._have_info = False

    def have_context(self) -> bool:
        return self._have_context

    def have_extension(self, extension: str) -> bool:
        """Determine if an OpenGL extension is available.

        Args:
            extension:
                The name of the extension to test for, including its ``GL_`` prefix.

        Returns:
            True if the extension is provided by the driver.
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return extension in self.extensions

    def get_extensions(self) -> set[str]:
        """Get a set of available OpenGL extensions."""
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.extensions

    def get_version(self) -> tuple[int, int]:
        """Get the current major and minor version of OpenGL."""
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.major_version, self.minor_version

    def get_version_string(self) -> str:
        """Get the current OpenGL version string."""
        if not self._have_context:
            warnings.warn('No GL context created yet.')
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
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        if not self.major_version and not self.minor_version:
            return False

        return (self.major_version > major or
                (self.major_version == major and self.minor_version >= minor) or
                (self.major_version == major and self.minor_version == minor))

    def get_renderer(self) -> str:
        """Determine the renderer string of the OpenGL context."""
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.renderer

    def get_vendor(self) -> str:
        """Determine the vendor string of the OpenGL context."""
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.vendor

    def get_opengl_api(self) -> str:
        """Determine the OpenGL API version.

        Usually ``gl`` or ``gles``.
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.opengl_api


# Single instance useful for apps with only a single context
# (or all contexts have the same GL driver, a common case).
_gl_info = GLInfo()

get_extensions = _gl_info.get_extensions
get_version = _gl_info.get_version
get_version_string = _gl_info.get_version_string
have_version = _gl_info.have_version
get_renderer = _gl_info.get_renderer
get_vendor = _gl_info.get_vendor
get_opengl_api = _gl_info.get_opengl_api
have_extension = _gl_info.have_extension
have_context = _gl_info.have_context
remove_active_context = _gl_info.remove_active_context
set_active_context = _gl_info.set_active_context
