import sys


def colorbyte(color):
    if sys.version.startswith('2'):
        return '%c' % color
    else:
        return bytes((color,))

