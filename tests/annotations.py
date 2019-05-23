from builtins import object

import sys

import pytest
import pyglet
from pyglet.gl import gl_info


# Platform identifiers
class Platform(object):
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


def require_platform(platform):
    """
    Only run the test on the given platform(s), skip on other platforms.

    :param list(str) platform: A list of platform identifiers as returned by
        :data:`pyglet.options`. See also :class:`tests.annotations.Platform`.
    """
    return pytest.mark.skipif(pyglet.compat_platform not in platform,
                              reason='requires platform: %s' % str(platform))


def skip_platform(platform):
    """
    Skip test on the given platform(s).

    :param list(str) platform: A list of platform identifiers as returned by
        :data:`pyglet.options`. See also :class:`tests.annotations.Platform`.
    """
    return pytest.mark.skipif(pyglet.compat_platform in platform,
                              reason='not supported for platform: %s' % str(platform))


def require_gl_extension(extension):
    """
    Skip the test if the given GL extension is not available.

    :param str extension: Name of the extension required.
    """
    return pytest.mark.skipif(not gl_info.have_extension(extension),
                              reason='Tests requires GL extension {0}'.format(extension))


def require_python_version(version):
    """
    Skip test on older Python versions.

    :param tuple version: The major, minor Python version as a tuple.
    """
    return pytest.mark.skipif(sys.version_info < version,
                              reason="Test require at least Python version {0}".format(version))
