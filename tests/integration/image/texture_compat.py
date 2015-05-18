"""Python 2/3 compatibility functions for texture tests."""
from builtins import bytes
import sys


def colorbyte(color):
    if sys.version.startswith('2'):
        return '%c' % color
    else:
        return bytes((color,))

