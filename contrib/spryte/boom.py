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

layer = spryte.Layer()
booms = []
def again(sprite=None):
    if sprite:
        sprite.delete()
    booms.append(spryte.AnimatedSprite('explosion.png', 2, 8, layer,
        win.width*random.random(), win.height*random.random(),
        random.random()/20 + .02, callback=again))
    booms[:] = [boom for boom in booms if not boom.finished]

again()

while not win.has_exit:
    clock.tick()
    win.dispatch_events()

    if len(booms) < NUM_BOOMS: again()

    win.clear()
    layer.draw()
    fps.draw()
    win.flip()
win.close()
