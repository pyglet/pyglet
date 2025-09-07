#!/usr/bin/env python
"""Display an image.

Usage::

    display.py <filename>

A checkerboard background is visible behind any transparent areas.
"""
import sys

import pyglet

from pyglet.image import CheckerImagePattern
from pyglet.graphics import Texture

window = pyglet.window.Window(visible=False, resizable=True)


@window.event
def on_draw():
    window.clear()
    batch.draw()


@window.event
def on_resize(width, height):
    # Scale the image Sprite to fit inside the Window dimensions:
    image_sprite.scale = min(height / img.height, width / img.width)
    # Make sure the image Sprite is centered in the Window:
    image_sprite.position = width // 2, height // 2, image_sprite.z


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    filename = sys.argv[1]

    img = pyglet.image.load(filename)
    img.anchor_x = img.width // 2
    img.anchor_y = img.height // 2

    batch = pyglet.graphics.Batch()
    image_group = pyglet.graphics.Group(order=1)
    background_group = pyglet.graphics.Group(order=0)

    # Create a background texture using ImageData with a simple checkered pattern:
    background_texture = Texture.create_from_image(image_data=pyglet.image.create(32, 32, CheckerImagePattern()))

    # TODO: remove this hack:
    background_texture.tex_coords = [c * 100 for c in background_texture.tex_coords]

    # Make Sprites so the background and image data can be displayed & manipulated:
    image_sprite = pyglet.sprite.Sprite(img=img, batch=batch, group=image_group)
    background_sprite = pyglet.sprite.Sprite(img=background_texture, batch=batch, group=background_group)

    # TODO: remove this hack:
    background_sprite.scale = 100

    window.width = img.width
    window.height = img.height
    window.set_visible()

    pyglet.app.run()
