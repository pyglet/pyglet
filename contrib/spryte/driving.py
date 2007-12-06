import os
import math

from pyglet import window
#from pyglet.window.event import *
from pyglet.window import key
from pyglet import clock

import spryte, tilemap

win = window.Window(vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

tiles = [
    [ 0,  1,  1,  1,  2,  3],
    [ 5,  6, 16, 16,  7,  8],
    [ 5,  8,  9,  9,  5,  8],
    [ 5,  8,  9,  9,  5,  8],
    [10, 11,  1,  1, 12, 13],
    [15, 16, 16, 16, 17, 18],
]
m = tilemap.Map.from_imagegrid('road-tiles.png', 4, 5, tiles)

layer = spryte.Layer()
car = spryte.Sprite('car.png', layer, 0, 0, rothandle=(16, 16))

keyboard = key.KeyStateHandler()
win.push_handlers(keyboard)

def animate(dt):
    # update car rotation & speed
    r = car.rotation
    r += (keyboard[key.LEFT] - keyboard[key.RIGHT]) * 5 * dt
    if r < 0: r += math.pi * 2
    elif r > math.pi * 2: r -= math.pi * 2
    car.rotation = r
    car.dy = (keyboard[key.UP] - keyboard[key.DOWN]) * 200 * dt

    # ... and the rest
    car.update_kinematics(dt)
clock.schedule(animate)

while not win.has_exit:
    dt = clock.tick()
    win.dispatch_events()

    m.draw()
    layer.draw()
    fps.draw()
    win.flip()
win.close()
