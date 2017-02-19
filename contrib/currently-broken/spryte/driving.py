import os
import math

from pyglet import window
from pyglet import resource
from pyglet import image
from pyglet.window import key
from pyglet import clock

import spryte
import view

win = window.Window(vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

map = [
    [ 0,  1,  1,  1,  2,  3],
    [ 5,  6, 16, 16,  7,  8],
    [ 5,  8,  9,  9,  5,  8],
    [ 5,  8,  9,  9,  5,  8],
    [ 5,  8,  9,  9,  5,  8],
    [ 5,  8,  9,  9,  5,  8],
    [ 5,  8,  9,  9,  5,  8],
    [ 5,  8,  9,  9,  5,  8],
    [10, 11,  1,  1, 12, 13],
    [15, 16, 16, 16, 17, 18],
]

v = view.View.for_window(win)
tiles = resource.image('road-tiles.png')
tiles = image.ImageGrid(tiles, 4, 5)
v.add_map(tiles, map)
car = resource.image('car.png')
car.anchor_x = 16
car.anchor_y = 20
car = v.add_sprite(car, 64, 64, z=1)

keyboard = key.KeyStateHandler()
win.push_handlers(keyboard)

# mouse picking ... needs to be in a different example
def f(x, y, buttons, modifiers):
    print (x, y)
car.on_mouse_press = f
win.push_handlers(v.get_layer(z=1))

def animate(dt):
    # update car rotation & speed
    r = car.rotation
    r += (keyboard[key.RIGHT] - keyboard[key.LEFT]) * 200 * dt
    if r < 0: r += 360
    elif r > 360: r -= 360
    car.rotation = r
    car.speed = (keyboard[key.UP] - keyboard[key.DOWN]) * 300 * dt

    # ... and the rest
    spryte.update_kinematics(car, dt)

    v.focus = car.position
clock.schedule(animate)

while not win.has_exit:
    dt = clock.tick()
    win.dispatch_events()
    win.clear()
    v.draw()
    fps.draw()
    win.flip()
win.close()

