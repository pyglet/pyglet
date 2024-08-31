"""An example of sorting sprites using many ordered groups."""
from __future__ import annotations

import math
import random

import pyglet

#pyglet.options.debug_gl = False

window = pyglet.window.Window(height=720, vsync=False)
fps = pyglet.window.FPSDisplay(window)

# Set example resource path.
pyglet.resource.path = ['../../examples/resources']
pyglet.resource.reindex()

image = pyglet.resource.image("pyglet.png")
# batch = pyglet.graphics.Batch()
batch = pyglet.experimental.graphics.Batch()

sprites = []

groups = []
for i in range(window.height + 1):
    group = pyglet.graphics.Group(i)
    groups.append(group)


def make_sprite(zvalue):
    sprite = pyglet.sprite.Sprite(image, x=0, y=0, batch=batch, group=groups[i])
    # Random color multiplier.
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    # Add sprites to keep in memory, like a list. Otherwise, they will get GC'd when out of scope.
    sprite.scale = 0.25
    sprites.append(sprite)


sprite_count = 60
for i in range(sprite_count):
    make_sprite(i)


global elapsed
elapsed = 0


def update(dt):
    global elapsed
    for i, sprite in enumerate(sprites):
        sprite.update(x=i * .75 * (sprite.width - 15),
                      y=.35 * window.height * (1 + math.cos(2 * elapsed + i * math.pi / sprite_count)))
        sprite.group = groups[int(sprite.y)]

    elapsed += dt


pyglet.clock.schedule_interval(update, 1 / 60.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()
    fps.draw()


pyglet.app.run(0)
