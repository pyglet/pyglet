import os
import math

from pyglet import window
from pyglet.window import key
from pyglet import clock

import view

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

v = view.View.from_window(win)
v.add_map('road-tiles.png', 4, 5, tiles)
car = v.add_sprite('car.png', 0, 0, z=1, rothandle=(16, 16))

keyboard = key.KeyStateHandler()
win.push_handlers(keyboard)

def animate(dt):
    # update car rotation & speed
    r = car.rotation
    r += (keyboard[key.LEFT] - keyboard[key.RIGHT]) * 200 * dt
    if r < 0: r += 360
    elif r > 360: r -= 360
    car.rotation = r
    car.dy = (keyboard[key.UP] - keyboard[key.DOWN]) * 300 * dt

    # ... and the rest
    car.update_kinematics(dt)
    v.focus = car.pos
clock.schedule(animate)

while not win.has_exit:
    dt = clock.tick()
    win.dispatch_events()
    win.clear()
    v.draw()
    fps.draw()
    win.flip()
win.close()

