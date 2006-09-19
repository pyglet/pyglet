#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window
from pyglet.window.event import *
import time

from pyglet.GL.VERSION_1_1 import *
import ctypes
import pyglet.GL
from pyglet import clock

gluPerspective = pyglet.GL.get_function('gluPerspective', [ctypes.c_float,
    ctypes.c_float, ctypes.c_float, ctypes.c_float], ctypes.c_int)

factory = pyglet.window.WindowFactory()
factory.config._attributes['doublebuffer'] = 1
w1 = factory.create(width=200, height=200)
glClearColor(1, 1, 1, 1)
glClear(GL_COLOR_BUFFER_BIT)
glFlush()
w1.flip()

class ExitHandler(object):
    running = True
    def on_close(self):
        self.running = False
    def on_keypress(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_ESCAPE:
            self.running = False
        return EVENT_UNHANDLED
exit_handler = ExitHandler()
w1.push_handlers(exit_handler)

c = clock.Clock()

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(60., 1., 1., 100.)
glMatrixMode(GL_MODELVIEW)
glColor4f(.5, .5, .5, .5)

r = 0
while exit_handler.running:
    c.set_fps(60)
    w1.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    r += 1
    if r > 360: r = 0
    glRotatef(r, 0, 0, 1)
    glBegin(GL_QUADS)
    glVertex3f(-1., -1., -5.)
    glVertex3f(-1., 1., -5.)
    glVertex3f(1., 1., -5.)
    glVertex3f(1., -1., -5.)
    glEnd()

    w1.flip()

