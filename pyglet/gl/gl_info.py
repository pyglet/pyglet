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
import warnings

from ctypes import c_char_p, cast

from pyglet.gl.gl import GL_EXTENSIONS, GL_RENDERER, GL_VENDOR, GL_VERSION
from pyglet.gl.gl import GL_MAJOR_VERSION, GL_MINOR_VERSION, GLint
from pyglet.gl.lib import GLException
from pyglet.util import asstr


def _get_number(parameter):
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
    _have_context = False
    vendor = ''
    renderer = ''
    version = '0.0'
    major_version = 0
    minor_version = 0
    opengl_api = 'gl'
    extensions = set()

    _have_info = False

    def set_active_context(self):
        """Store information for the currently active context.

        This method is called automatically for the default context.
        """
        from pyglet.gl.gl import glGetString, glGetStringi, GL_NUM_EXTENSIONS

        self._have_context = True
        if not self._have_info:
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
                pass    # GL3 is likely not available

            self._have_info = True

    def remove_active_context(self):
        self._have_context = False
        self._have_info = False

    def have_context(self):
        return self._have_context

    def have_extension(self, extension):
        """Determine if an OpenGL extension is available.

        :Parameters:
            `extension` : str
                The name of the extension to test for, including its
                ``GL_`` prefix.

        :return: True if the extension is provided by the driver.
        :rtype: bool
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return extension in self.extensions

    def get_extensions(self):
        """Get a list of available OpenGL extensions.

        :return: a list of the available extensions.
        :rtype: list of str
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.extensions

    def get_version(self):
        """Get the current OpenGL version.

        :return: The major and minor version as a tuple
        :rtype: tuple
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.major_version, self.minor_version

    def get_version_string(self):
        """Get the current OpenGL version string.

        :return: The OpenGL version string
        :rtype: str
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.version

    def have_version(self, major, minor=0):
        """Determine if a version of OpenGL is supported.

        :Parameters:
            `major` : int
                The major revision number (typically 1 or 2).
            `minor` : int
                The minor revision number.

        :rtype: bool
        :return: True if the requested or a later version is supported.
        """

        if not self._have_context:
            warnings.warn('No GL context created yet.')
        if not self.major_version and not self.minor_version:
            return False

        return (self.major_version > major or
                (self.major_version == major and self.minor_version >= minor) or
                (self.major_version == major and self.minor_version == minor))

    def get_renderer(self):
        """Determine the renderer string of the OpenGL context.

        :rtype: str
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.renderer

    def get_vendor(self):
        """Determine the vendor string of the OpenGL context.

        :rtype: str
        """
        if not self._have_context:
            warnings.warn('No GL context created yet.')
        return self.vendor

    def get_opengl_api(self):
        """Determine the OpenGL API version.
        Usually ``gl`` or ``gles``.

        :rtype: str
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
