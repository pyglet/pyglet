"""Example on how to draw specific groups in a Batch.

This can be useful if you need to draw groups during runtime; for example drawing
into an offscreen framebuffer for effects.
"""
from __future__ import annotations

import random

import pyglet
from pyglet.graphics import Group

window = pyglet.window.Window(height=720, vsync=False)
fps = pyglet.window.FPSDisplay(window)

# Set example resource path.
pyglet.resource.path = ['../../examples/resources']
pyglet.resource.reindex()

image = pyglet.resource.image("pyglet.png")
# batch = pyglet.graphics.Batch()
batch = pyglet.experimental.graphics.Batch(group_draw=True)

scales = [1.0, 0.75, 0.5, 0.25]

class DistinctGroup(pyglet.graphics.Group):
    """A group that will be distinct from another."""
    def __eq__(self, other: Group) -> bool:
        return (self.__class__ is other.__class__ and
                self._order == other.order and
                self.parent == other.parent)

    def __hash__(self):
        return hash((id(self), self._order, self.parent))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(order={self._order}, id={id(self)})"

group1 = DistinctGroup()
group2 = DistinctGroup()

print("Groups:", group1, group2)

sprites = []
# Create 1000 sprites at various scales.
for i in range(100):
    sprite = pyglet.sprite.Sprite(image,
                                  x=random.randint(0, window.width),
                                  y=random.randint(0, window.height),
                                  group=group1 if i % 2 else group2,
                                  batch=batch)  # specify the batch to enter the sprites in.

    # Randomize scale.
    sprite.scale = random.choice(scales)

    # Random color multiplier.
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # Add sprites to keep in memory, like a list. Otherwise they will get GC'd when out of scope.
    sprites.append(sprite)


groups_to_draw = set()
@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.A:
        if group1 not in groups_to_draw:
            groups_to_draw.add(group1)
    elif symbol == pyglet.window.key.D:
        if group2 not in groups_to_draw:
            groups_to_draw.add(group2)
    elif symbol == pyglet.window.key.SPACE:
        groups_to_draw.clear()


@window.event
def on_draw():
    global groups_to_draw
    window.clear()
    if groups_to_draw:
        batch.draw_groups(*groups_to_draw)

print("Specify Drawing Specific Groups: \nPress the following keys:")
print("A: Add Group 1 to Draw List")
print("D: Add Group 2 to Draw List")
print("SPACE: Clear all groups.")



pyglet.app.run()

