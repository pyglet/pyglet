import sys
import random
import math

from pyglet import window
from pyglet import clock
from pyglet import resource

import spryte

NUM_CARS = 100
if len(sys.argv) > 1:
    NUM_CARS = int(sys.argv[1])

win = window.Window(vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

cars = spryte.SpriteBatch()
car = resource.image('car.png')
car.anchor_x = 16
car.anchor_y = 20
for i in range(NUM_CARS):
    s = spryte.Sprite(car,
        win.width*random.random(), win.height*random.random(),
        batch=cars, dr=-45 + random.random()*90)

while not win.has_exit:
    win.dispatch_events()
    clock.tick()

    win.clear()
    for car in cars:
        car.rotation = (car.rotation + car.dr) % 360
    cars.draw()
    fps.draw()
    win.flip()

