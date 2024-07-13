"""Information about version and extensions of current GLX implementation.

Usage::

    from pyglet.gl import glx_info

    if glx_info.have_extension('GLX_NV_float_buffer'):
        # ...

Or, if using more than one display::

    from pyglet.gl.glx_info import GLXInfo

    info = GLXInfo(window._display)
    if info.get_server_vendor() == 'ATI':
        # ...

"""

from __future__ import annotations

from ctypes import byref, c_int
from typing import TYPE_CHECKING

from pyglet.gl.glx import (
    GLX_EXTENSIONS,
    GLX_VENDOR,
    GLX_VERSION,
    glXGetClientString,
    glXQueryExtension,
    glXQueryExtensionsString,
    glXQueryServerString,
    glXQueryVersion,
)

from pyglet.util import asstr

if TYPE_CHECKING:
    from pyglet.libs.x11.xlib import Display


class GLXInfoException(Exception):  # noqa: D101, N818
    pass


class GLXInfo:  # noqa: D101
    def __init__(self, display: Display | None = None) -> None:  # noqa: D107
        # Set default display if not set
        if display and not _glx_info.display:
            _glx_info.set_display(display)

        self.display = display

    def set_display(self, display: Display) -> None:
        self.display = display

    def check_display(self) -> None:
        if not self.display:
            msg = 'No X11 display has been set yet.'
            raise GLXInfoException(msg)

    def have_version(self, major: int, minor: int = 0) -> bool:
        self.check_display()
        if not glXQueryExtension(self.display, None, None):
            msg = 'pyglet requires an X server with GLX'
            raise GLXInfoException(msg)

        server_version = self.get_server_version().split()[0]
        client_version = self.get_client_version().split()[0]

        server = [int(i) for i in server_version.split('.')]
        client = [int(i) for i in client_version.split('.')]
        return (tuple(server) >= (major, minor) and
                tuple(client) >= (major, minor))

    def get_server_vendor(self) -> str:
        self.check_display()
        return asstr(glXQueryServerString(self.display, 0, GLX_VENDOR))

    def get_server_version(self) -> str:
        # glXQueryServerString was introduced in GLX 1.1, so we need to use the
        # 1.0 function here which queries the server implementation for its
        # version.
        self.check_display()
        major = c_int()
        minor = c_int()
        if not glXQueryVersion(self.display, byref(major), byref(minor)):
            msg = 'Could not determine GLX server version'
            raise GLXInfoException(msg)
        return f'{major.value}.{minor.value}'

    def get_server_extensions(self) -> list[str]:
        self.check_display()
        return asstr(glXQueryServerString(self.display, 0, GLX_EXTENSIONS)).split()

    def get_client_vendor(self) -> str:
        self.check_display()
        return asstr(glXGetClientString(self.display, GLX_VENDOR))

    def get_client_version(self) -> str:
        self.check_display()
        return asstr(glXGetClientString(self.display, GLX_VERSION))

    def get_client_extensions(self) -> list[str]:
        self.check_display()
        return asstr(glXGetClientString(self.display, GLX_EXTENSIONS)).split()

    def get_extensions(self) -> list[str]:
        self.check_display()
        return asstr(glXQueryExtensionsString(self.display, 0)).split()

    def have_extension(self, extension: str) -> bool:
        self.check_display()
        if not self.have_version(1, 1):
            return False
        return extension in self.get_extensions()


# Single instance suitable for apps that use only a single display.
_glx_info = GLXInfo()

set_display = _glx_info.set_display
check_display = _glx_info.check_display
have_version = _glx_info.have_version
get_server_vendor = _glx_info.get_server_vendor
get_server_version = _glx_info.get_server_version
get_server_extensions = _glx_info.get_server_extensions
get_client_vendor = _glx_info.get_client_vendor
get_client_version = _glx_info.get_client_version
get_client_extensions = _glx_info.get_client_extensions
get_extensions = _glx_info.get_extensions
have_extension = _glx_info.have_extension
