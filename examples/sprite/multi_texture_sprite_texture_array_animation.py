"""Animated multi-texture sprite example using a single TextureArray."""
from __future__ import annotations

import pyglet


window = pyglet.window.Window(width=400, height=400)

# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

batch = pyglet.graphics.Batch()

# Load source images as CPU-side image data, then split into frames.
brick_gray_image = pyglet.resource.image("Brick1Gray.png")
brick_blue_image = pyglet.resource.image("Brick1Blue.png")
brick_crack_image = pyglet.resource.image("Brick1Crack3.png")

brick_gray_grid = pyglet.image.ImageGrid(brick_gray_image, 1, 6)
brick_blue_grid = pyglet.image.ImageGrid(brick_blue_image, 1, 6)
crack_grid = pyglet.image.ImageGrid(brick_crack_image, 1, 3)

# Pack all frames into one TextureArray.
all_frames = [*brick_gray_grid, *brick_blue_grid, *crack_grid]
shared_texture_array = pyglet.graphics.TextureArray.create_for_images(all_frames)

# Build animations from slices of the same TextureArray.
brick_gray_animation = pyglet.image.Animation.from_image_sequence(shared_texture_array[0:6], 1.0 / 10.0)
brick_blue_animation = pyglet.image.Animation.from_image_sequence(shared_texture_array[6:12], 1.0 / 10.0)
crack_animation = pyglet.image.Animation.from_image_sequence(shared_texture_array[12:15], 1.0, False)

sprite = pyglet.sprite.MultiTextureSprite({'brick': brick_blue_animation, 'crack': crack_animation},
                                          x=0, y=0, batch=batch)
sprite2 = pyglet.sprite.MultiTextureSprite({'brick': brick_blue_animation, 'crack': crack_animation},
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
    sprite.set_layer('brick', brick_gray_animation)


pyglet.clock.schedule_once(advance_crack, 1.0)
pyglet.clock.schedule_once(toggle_pause, 3.5)
pyglet.clock.schedule_once(swap_brick_layer, 5.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
