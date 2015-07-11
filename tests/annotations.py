"""
Annotations for test cases
==========================

Use these to control running test cases only on specific platforms.

Later some test filtering could be added.
"""
from builtins import object

import pyglet
import unittest


# Platform identifiers
class Platform(object):
    LINUX = ('linux-compat', 'linux2', 'linux')
    WINDOWS = ('win32', 'cygwin')
    OSX = ('darwin',)


def require_platform(platform):
    """
    Only run the test on the given platform(s). Specify multiple platforms using +.
    """
    if pyglet.compat_platform in platform:
        return lambda f: f
    else:
        return unittest.skip('Skipped for current platform')

def skip_platform(platform):
    """
    Do not run on the given platform(s). Specify multiple platforms using +.
    """
    if pyglet.compat_platform in platform:
        return unittest.skip('Skipped for current platform')
    else:
        return lambda f: f
