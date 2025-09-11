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

try:
    # Will be found in the pyodide VFS.
    image = pyglet.resource.image("pyglet.png")
except pyglet.resource.ResourceNotFoundException:
    # Could not find the image, check your path.
    image = pyglet.image.SolidColorImagePattern((255, 0, 0, 255)).create_image(64, 64)

image.anchor_x = image.width // 2
image.anchor_y = image.height // 2

sprites = [pyglet.sprite.Sprite(image,
                                x=random.randint(0, window.width),
                                y=random.randint(0, window.height), batch=batch)]

@window.event
def on_key_press(symbol, modifiers):
    sprite = pyglet.sprite.Sprite(
        image, x=random.randint(0, window.width), y=random.randint(0, window.height), batch=batch
    )
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    sprites.append(sprite)


@window.event
def on_draw():
    window.clear()
    batch.draw()

# Pyodide 0.27.7 has a memory leak with asyncio. Use pyglet.app.run(None) until it's resolved.
if pyglet.compat_platform == "emscripten":
    # None will use requestAnimationFrame as a base for timer scheduling and rendering.
    pyglet.app.run(None)
else:
    pyglet.app.run()
