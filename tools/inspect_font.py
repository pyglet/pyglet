#!/usr/bin/python
# $Id:$

"""Display font information.

Usage::

    inspect_font.py <filename> [<filename> ...]
"""

import sys
from pyglet.font import ttf


def inspect_font(filename):
    try:
        info = ttf.TruetypeInfo(filename)
        print('{0}:'.format(filename))
        print(info.get_name('family'))
        print('bold=%r' % info.is_bold())
        print('italic=%r' % info.is_italic())
    except:
        print("%s could not be identified.  It is probably not a TrueType or "
              "OpenType font.  However, pyglet may still be able to load it "
              "on some platforms." % filename)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
    for file_name in sys.argv[1:]:
        inspect_font(file_name)
