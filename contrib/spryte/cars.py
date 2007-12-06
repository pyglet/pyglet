import sys
import random
import math

from pyglet import window, clock, gl, event

import spryte

NUM_BOOMS = 100
if len(sys.argv) > 1:
    NUM_BOOMS = int(sys.argv[1])

win = window.Window(vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

layer = spryte.Layer()
cars = [
    spryte.Sprite('car.png', layer,
        win.width*random.random(), win.height*random.random(),
        rothandle = (16, 16), dr=-.25 + random.random()/2)
    for x in range(1000)
]

while not win.has_exit:
    clock.tick()
    win.dispatch_events()

    win.clear()
    for car in cars:
        r = car.rotation
        r += car.dr
        if r < 0: r += math.pi * 2
        elif r > math.pi * 2: r -= math.pi * 2
        car.rotation = r
    layer.draw()
    fps.draw()
    win.flip()

