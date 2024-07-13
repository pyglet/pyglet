#!/usr/bin/env python
"""Display an image.

Usage::

    display.py <filename>

A checkerboard background is visible behind any transparent areas.
"""


import sys

import pyglet
from pyglet.gl import (
    glEnable,
    glBlendFunc,
    GL_BLEND,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
)

window = pyglet.window.Window(visible=False, resizable=True)


@window.event
def on_draw():
    background.blit_tiled(0, 0, 0, window.width, window.height)
    img.blit(window.width // 2, window.height // 2, 0)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    filename = sys.argv[1]

    img = pyglet.image.load(filename)
    img.anchor_x = img.width // 2
    img.anchor_y = img.height // 2

    checks = pyglet.image.create(32, 32, pyglet.image.CheckerImagePattern())
    background = pyglet.image.TileableTexture.create_for_image(checks)

    # Enable alpha blending, required for image.blit.
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    window.width = img.width
    window.height = img.height
    window.set_visible()

    pyglet.app.run()
