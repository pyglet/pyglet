import sys
import random

from pyglet import window, clock, gl, event
from pyglet.window import key

import spryte

NUM_BOOMS = 100
if len(sys.argv) > 1:
    NUM_BOOMS = int(sys.argv[1])

win = window.Window(vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

booms = spryte.Layer()
def again(sprite=None):
    if sprite:
        sprite.delete()
    spryte.AnimatedSprite('explosion.png', 2, 8, booms,
        win.width*random.random(), win.height*random.random(),
        random.random()/20 + .02, callback=again)

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
