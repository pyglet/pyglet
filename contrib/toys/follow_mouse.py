"""Code by Richard Jones, released into the public domain.

Inspired by http://screamyguy.net/lines/index.htm

This code uses a single drawing buffer so that successive drawing passes
may be used to create the line fading effect. The fading is achieved
by drawing a translucent black quad over the entire scene before drawing
the next line segment.

Note: when working with a single buffer it is always a good idea to
glFlush() when you've finished your rendering.
"""


import sys
import random

import pyglet
from pyglet.gl import (
    glEnable,
    glBlendFunc,
    glFlush,
    Config,
    GL_BLEND,
    GL_LINE_SMOOTH,
    GL_LINES,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
)

# open a single-buffered window so we can do cheap accumulation
config = Config(double_buffer=False)
window = pyglet.window.Window(fullscreen='-fs' in sys.argv, config=config)


class Line:
    batch = pyglet.graphics.Batch()
    lines = batch.add(100, GL_LINES, None, ('position3f', (0.0,) * 300), ('colors4Bn', (255, ) * 400))
    black = pyglet.shapes.Rectangle(0, 0, window.width, window.height, color=(0, 0, 0), batch=batch)
    black.opacity = 32
    unallocated = list(range(100))
    active = []

    mouse_x = mouse_y = 0

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
        cls.batch.draw()
        glFlush()

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
        for n, line in enumerate(cls.active):
            line.update(dt)
            cls.lines.position[n*6:n*6+6] = [line.lx, line.ly, 0, line.x, line.y, 0]


glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_LINE_SMOOTH)


pyglet.clock.schedule_interval(Line.tick, 1/30)
window.push_handlers(Line)

pyglet.app.run()
