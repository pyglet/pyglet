"""Animated multi-texture sprite example."""
from __future__ import annotations

import pyglet


window = pyglet.window.Window(width=400, height=400)

# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

batch = pyglet.graphics.Batch()

brick_gray_texture = pyglet.resource.texture("Brick1Gray.png", atlas=False)
brick_gray_grid = pyglet.graphics.TextureGrid(brick_gray_texture, 1, 6)
brick_gray = pyglet.image.Animation.from_image_sequence(brick_gray_grid, 1.0 / 10.0)

blue_brick_texture = pyglet.resource.texture("Brick1Blue.png", atlas=False)
brick_grid = pyglet.graphics.TextureGrid(blue_brick_texture, 1, 6)
brick_animation = pyglet.image.Animation.from_image_sequence(brick_grid, 1.0 / 10.0)

brick_crack_texture = pyglet.resource.texture("Brick1Crack3.png", atlas=False)
crack_grid = pyglet.graphics.TextureGrid(brick_crack_texture, 1, 3)
crack_animation = pyglet.image.Animation.from_image_sequence(crack_grid, 1.0, False)

sprite = pyglet.sprite.MultiTextureSprite({'brick': brick_animation, 'crack': crack_animation}, x=0, y=0, batch=batch)
sprite2 = pyglet.sprite.MultiTextureSprite({'brick': brick_animation, 'crack': crack_animation},
                                           x=100, y=100, batch=batch)

crack_frame = 0


def advance_crack(_dt):
    global crack_frame  # noqa: PLW0603
    crack_frame = (crack_frame + 1) % 3
    sprite.set_frame_index('crack', crack_frame)
    pyglet.clock.schedule_once(advance_crack, 1.0)


def toggle_pause(_dt):
    sprite2.paused = not sprite2.paused
    pyglet.clock.schedule_once(toggle_pause, 3.5)


def swap_brick_layer(_dt):
    sprite.set_layer('brick', brick_gray)


pyglet.clock.schedule_once(advance_crack, 1.0)
pyglet.clock.schedule_once(toggle_pause, 3.5)
pyglet.clock.schedule_once(swap_brick_layer, 5.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
