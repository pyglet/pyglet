#!/usr/bin/env python

'''Display an image.

Usage::

    display.py <filename>

A checkerboard background is visible behind any transparent areas of the
image.
'''

import sys

from pyglet.gl import *
from pyglet import window
from pyglet import image

if __name__ == '__main__':
    if len(sys.argv) != 1:
        print __doc__
        sys.exit(1)

    filename = sys.argv[1]

    w = window.Window(visible=False, resizable=True)
    img = image.load(filename).texture

    checks = image.create(32, 32, image.CheckerImagePattern())
    background = image.TileableTexture.create_for_image(checks)

    w.width = img.width
    w.height = img.height
    w.set_visible()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    while not w.has_exit:
        w.dispatch_events()
        
        background.blit_tiled(0, 0, 0, w.width, w.height)
        img.blit(0, 0, 0)
        w.flip()

