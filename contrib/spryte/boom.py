import sys
import random

from pyglet import window
from pyglet import image
from pyglet import clock
from pyglet import resource

import spryte

NUM_BOOMS = 20
if len(sys.argv) > 1:
    NUM_BOOMS = int(sys.argv[1])

win = window.Window(vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

explosions = spryte.SpriteBatch()
explosion_images = resource.image('explosion.png')
explosion_images = image.ImageGrid(explosion_images, 2, 8)
explosion_animation = image.Animation.from_image_sequence(explosion_images,
    .001, loop=False)

class EffectSprite(spryte.Sprite):
    def on_animation_end(self):
        self.delete()
        again()

booms = spryte.SpriteBatch()
def again():
    EffectSprite(explosion_animation,
        win.width*random.random(), win.height*random.random(),
        batch=booms)

again()

while not win.has_exit:
    clock.tick()
    win.dispatch_events()

    if len(booms) < NUM_BOOMS: again()

    win.clear()
    booms.draw()
    fps.draw()
    win.flip()
win.close()

