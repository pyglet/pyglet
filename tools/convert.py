#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import getopt
import os.path
import sys
import textwrap

import pyglet.dds
import pyglet.image
import pyglet.window

def usage():
    print textwrap.dedent('''
        convert.py <input-file> <output-file>
        ''')

def main(args):
    del args[0]
    pyglet.window.set_window()   # need a window for OpenGL context

    if len(args) < 2:
        usage()
        sys.exit()

    srcimage = args[0]
    srctype = os.path.splitext(srcimage)[1].lower()
    destimage = args[1]
    desttype = os.path.splitext(destimage)[1].lower()

    if srctype == '.dds':
        texture = pyglet.dds.load_dds(srcimage)
    else:
        texture = pyglet.image.Texture.from_surface(pyglet.image.load(srcimage))

    print texture.size

    if desttype == '.dds':
        raise NotImplementedError, 'TODO: save compressed texture'
    else:
        pyglet.image.save(texture, destimage)


if __name__ == '__main__':
    main(sys.argv)
