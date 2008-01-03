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

cars = spryte.Layer()
for x in range(1000):
    spryte.Sprite('car.png', cars,
        win.width*random.random(), win.height*random.random(),
        rothandle = (16, 16), dr=-45 + random.random()*90)

while not win.has_exit:
    clock.tick()
    win.dispatch_events()

    win.clear()
    for car in cars:
        car.rotation = (car.rotation + car.dr) % 360
    cars.draw()
    fps.draw()
    win.flip()

