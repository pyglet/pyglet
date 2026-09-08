from __future__ import annotations

import pyglet
import random

window = pyglet.window.Window()

batch = pyglet.graphics.Batch()

label = pyglet.text.Label('Press Any Key To Add A Sprite!',
                          font_size=24,
                          x=window.width // 2,
                          y=window.height // 2,
                          anchor_x='center',
                          anchor_y='center',
                          batch=batch)

# Packaged by ``resources`` in pyproject.toml and loaded from the Pyodide VFS.
image = pyglet.resource.image("pyglet.png")

sprites = [pyglet.sprite.Sprite(image,
                                x=random.randint(0, window.width),
                                y=random.randint(0, window.height),
                                anchor=(image.width // 2, image.height // 2), batch=batch)]

@window.event
def on_key_press(symbol, modifiers):
    sprite = pyglet.sprite.Sprite(
        image, x=random.randint(0, window.width), y=random.randint(0, window.height),
        anchor=(image.width // 2, image.height // 2), batch=batch
    )
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    sprites.append(sprite)


@window.event
def on_draw():
    window.clear()
    batch.draw()

pyglet.app.run()
