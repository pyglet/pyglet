'''
Code by Richard Jones, released into the public domain.

Inspired by http://screamyguy.net/lines/index.htm

This code uses a single drawing buffer so that successive drawing passes
may be used to create the line fading effect. The fading is achieved
by drawing a translucent black quad over the entire scene before drawing
the next line segment.

Note: when working with a single buffer it is always a good idea to
glFlush() when you've finished your rendering.
'''


import sys
import random

import pyglet
from pyglet.gl import *

# open a single-buffered window so we can do cheap accumulation
config = Config(double_buffer=False)
window = pyglet.window.Window(fullscreen='-fs' in sys.argv, config=config)

class Line(object):
    batch = pyglet.graphics.Batch()
    lines = batch.add(100, GL_LINES, None, ('v2f', (0.0,)  * 200), ('c4B', (255, ) * 400))
    unallocated = range(100)
    active = []

    def __init__(self):
        self.n = self.unallocated.pop()
        self.active.append(self)
        self.x = self.lx = random.randint(0, window.width)
        self.y = self.ly = random.randint(0, window.height)
        self.dx = random.randint(-70, 70)
        self.dy = random.randint(-70, 70)
        self.damping = random.random() * .15 + .8
        self.power = random.random() * .1 + .05

    def update(self, dt):
        # calculate my acceleration based on the distance to the mouse
        # pointer and my acceleration power
        dx2 = (self.x - self.mouse_x) / self.power
        dy2 = (self.y - self.mouse_y) / self.power

        # now figure my new velocity
        self.dx -= dx2 * dt
        self.dy -= dy2 * dt
        self.dx *= self.damping
        self.dy *= self.damping

        # calculate new line endpoints
        self.lx = self.x
        self.ly = self.y
        self.x += self.dx * dt
        self.y += self.dy * dt

    @classmethod
    def on_draw(cls):
        # darken the existing display a little
        glColor4f(0, 0, 0, .05)
        glRectf(0, 0, window.width, window.height)

        # render the new lines
        cls.batch.draw()

        glFlush()

    mouse_x = mouse_y = 0
    @classmethod
    def on_mouse_motion(cls, x, y, dx, dy):
        cls.mouse_x, cls.mouse_y = x, y

    @classmethod
    def tick(cls, dt):
        if len(cls.active) < 50 and random.random() < .1:
            cls()

        if len(cls.active) > 10 and random.random() < .01:
            line = cls.active.pop(0)
            cls.unallocated.append(line.n)

        # update line positions
        n = len(cls.active)
        for n, line in enumerate(cls.active):
            line.update(dt)
            cls.lines.vertices[n*4:n*4+4] = [line.lx, line.ly, line.x, line.y]

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_LINE_SMOOTH)

# need to set a FPS limit since we're not going to be limited by VSYNC in single-buffer mode
pyglet.clock.set_fps_limit(30)

pyglet.clock.schedule(Line.tick)
window.push_handlers(Line)
pyglet.app.run()

