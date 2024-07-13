#!/usr/bin/env python3

import pyglet
import pyglet.experimental

window = pyglet.window.Window()
window.set_size(400, 400)

pyglet.resource.path = ['../../examples/resources']
pyglet.resource.reindex()

# Batching allows rendering groups of objects all at once instead of drawing one by one.
batch = pyglet.graphics.Batch()

# Load 2 animation images to load onto our sprites
grid = pyglet.image.ImageGrid(pyglet.resource.image("Brick1Blue.png"),1, 6)
animation = pyglet.image.Animation.from_image_sequence(grid, 1.0 / 10.0)
gridcrack = pyglet.image.ImageGrid(pyglet.resource.image("Brick1Crack3.png"),1, 3)
animationcrack = pyglet.image.Animation.from_image_sequence(gridcrack, None, False)
shader_images = [animation, animationcrack]

sprite = pyglet.experimental.MultiTextureSprite(shader_images,
                                                x=0,
                                                y=0,
                                                batch=batch)
sprite2 = pyglet.experimental.MultiTextureSprite(shader_images,
                                                 x=100,
                                                 y=100,
                                                 batch=batch)

# For this sprite the kitten.jpg will be loaded into a seperate texture
# atlas from all of the other images.  The multi-texture sprite can
# handle this as well but just like normal sprites because the texture
# is different it will be grouped in a seperate draw call from the other
# sprites.
logo = pyglet.resource.image("pyglet.png")
kitten = pyglet.resource.image("kitten.jpg")
sprite3 = pyglet.experimental.MultiTextureSprite([kitten, logo],
                                                 x=150,
                                                 y=150,
                                                 batch=batch)
sprite3.scale = 0.2

f = 0

@window.event
def on_draw():
    window.clear()
    batch.draw()

def crack(dt):
    """Change frames for the second layer.
    """
    global f
    f = (f + 1) % 3
    sprite.set_frame_index(1,f)
    pyglet.clock.schedule_once(crack, 1.0)


pyglet.clock.schedule_once(crack, 1.0)

pyglet.app.run()
