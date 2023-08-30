from math import *

from pyglet import app, clock
from pyglet.shapes2d import Sector
from pyglet.math import Mat3, Vec2, Vec3
from pyglet import window

win = window.Window(400, 300, "test")
s = Sector(200, 150, 50, 60, 30, color=(255, 0, 0))
s.anchor_position = (10, 10)
s.rotation = 30

@win.event
def on_draw():
    win.clear()
    s.draw()

@win.event
def on_mouse_motion(x, y, dx, dy):
    if (x, y) in s:
        s.color = (255, 255, 0)
    else:
        s.color = (255, 0, 0)

def trans(x, y):
    center = Vec2(*s.position)
    point = Vec2(x, y) - Vec2(*s.anchor_position)
    p = (point - center).rotate(-radians(s.rotation))
    return center + p

def invert(x, y):
    center = Vec2(*s.position)
    rotated = (Vec2(x, y) - center).rotate(radians(s.rotation))
    anchor = Vec2(*s.anchor_position)
    return rotated + center + anchor

def update(dt):
    s.rotation += 1
    c.position = trans(250, 150)
    c.position = invert(*c.position)

if __name__ == "__main__":
    clock.schedule_interval(win.draw, 1 / 60)
    # clock.schedule_interval(update, 0.05)
    app.run()

