"""Display an image.

Usage::

    display.py <filename>

A grey background is visible behind any transparent areas.
"""
import sys

import pyglet


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

    # Make a batch to contain all drawable objects.
    # In this case, only a single Sprite will be in it:
    batch = pyglet.graphics.Batch()
    # Make a Sprite so that the image can be displayed & manipulated:
    image_sprite = pyglet.sprite.Sprite(img=img, batch=batch)

    # Set the initial Window size to match the image:
    window.width = img.width
    window.height = img.height
    window.set_visible()
    window.context.set_clear_color(0.4, 0.4, 0.4, 1.0)

    pyglet.app.run()
