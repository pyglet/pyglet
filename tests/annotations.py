from __future__ import annotations

import os
import sys

import pytest
import pyglet


# Platform identifiers
class Platform:
    """
    Predefined lists of identifiers for platforms. For use with
    :func:`.require_platform` and :func:`.skip_platform`. Combine platforms using +.
    """
    LINUX = ('linux-compat', 'linux2', 'linux')
    """Linux platforms"""

    WINDOWS = ('win32', 'cygwin')
    """MS Windows platforms"""

    OSX = ('darwin',)
    """Mac OS X platforms"""


class GraphicsAPI:
    GL3 = ("opengl", "gles3")
    GL2 = ("gl2", "gles2")
    GLES = ("gles2", "gles3")


def require_platform(platform: list[str]):
    """
    Only run the test on the given platform(s), skip on other platforms.

    Args:
         platform:
            A list of platform identifiers as returned by
            :data:`pyglet.options`. See also :class:`tests.annotations.Platform`.
    """
    return pytest.mark.skipif(pyglet.compat_platform not in platform,
                              reason=f'requires platform: {platform!s}')


def skip_platform(platform: list[str]):
    """
    Skip test on the given platform(s).

    Args:
        platform:
            A list of platform identifiers as returned by
            :data:`pyglet.options`. See also :class:`tests.annotations.Platform`.
    """
    return pytest.mark.skipif(pyglet.compat_platform in platform,
                              reason=f'not supported for platform: {platform!s}')


def require_gl_extension(extension):
    """
    Skip the test if the given GL extension is not available.

    :param str extension: Name of the extension required.
    """

    from pyglet.graphics.api import core
    return pytest.mark.skipif(not core.have_extension(extension),
                              reason=f'Tests requires GL extension {extension}')


def require_python_version(version: tuple[int, int]):
    """
    Skip test on older Python versions.

    Args:
        version: The major, minor Python version as a tuple.
    """
    return pytest.mark.skipif(sys.version_info < version,
                              reason=f"Test require at least Python version {version}")


def skip_if_continuous_integration():
    """
    Skip the test if being run under a Continuous Integration service.
    """
    return pytest.mark.skipif(any(key in os.environ for key in ['CI']),
                              reason="Test is unreliable, or unavailable under Continuous Integration ")


def require_graphics_api(backend: list[str]):
    """Specify a test is used with specific graphics API.

    Args:
        backend:
            The graphics API backend, as used by pyglet.options.backend.
    """
    return pytest.mark.skipif(pyglet.options.backend not in backend,
                              reason=f"Test requires graphics backend: '{backend}'")


def skip_graphics_api(backend: list[str]):
    """Skip the test if being run under a graphics API.

    Args:
        backend:
            The graphics API backend, as used by pyglet.options.backend.
    """
    return pytest.mark.skipif(pyglet.options.backend in backend,
                              reason=f"Not supported for graphics backend: '{backend}'")