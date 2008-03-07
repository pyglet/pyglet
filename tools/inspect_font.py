#!/usr/bin/python
# $Id:$

'''Display font information.

Usage::

    inspect_font.py <filename> [<filename> ...]
'''

import sys
from pyglet.font import ttf

def inspect_font(filename):
    info = ttf.TruetypeInfo(filename)
    print '%s:' % filename,
    print info.get_name('family'), 
    print 'bold=%r' % info.is_bold(),
    print 'italic=%r' % info.is_italic(),

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print __doc__
    for filename in sys.argv[1:]:
        inspect_font(filename)
