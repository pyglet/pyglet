"""An example of sorting sprites using the experimental SortedGroup."""
from __future__ import annotations

import math
import random

import pyglet

# pyglet.options.debug_gl = False

window = pyglet.window.Window(height=720, vsync=False)
fps = pyglet.window.FPSDisplay(window)
fps.label.color = (0, 255, 0)

pyglet.resource.path = ['../../examples/resources']
pyglet.resource.reindex()

image = pyglet.resource.image("pyglet.png")
batch = pyglet.experimental.graphics.Batch()

sprites = []

group = pyglet.experimental.graphics.SortedGroup()


def make_sprite(zvalue):
    sprite = pyglet.sprite.Sprite(image, x=0, y=0, batch=batch, group=group)
    # Random color multiplier.
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    # Add sprites to keep in memory, like a list. Otherwise, they will get GC'd when out of scope.
    sprite.scale = 0.25
    sprites.append(sprite)


sprite_count = 100
for i in range(sprite_count):
    make_sprite(i)

group.link_objects(sprites)

global elapsed
elapsed = 0


# @profile
def update(dt):
    global elapsed
    for i, sprite in enumerate(sprites):
        sprite.update(x=i * .15 * (sprite.width - 15),
                      y=.45 * window.height * (1 + math.cos(2 * elapsed + i * math.pi / sprite_count)))

    group.sort_objects(lambda s: int(s.y))
    elapsed += dt


pyglet.clock.schedule_interval(update, 1 / 60.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()
    fps.draw()


pyglet.app.run(0)
