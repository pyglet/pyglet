#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: gl_test.py 111 2006-10-20 06:39:12Z r1chardj0n3s $'

import pyglet.window
from pyglet.window.event import *
import time

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock

w1 = pyglet.window.Window(200, 200)

exit_handler = ExitHandler()
w1.push_handlers(exit_handler)

c = clock.Clock(60)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(60., 1., 1., 100.)

glMatrixMode(GL_MODELVIEW)
glClearColor(1, 1, 1, 1)
glColor4f(.5, .5, .5, .5)
r = 0
while not exit_handler.exit:
    c.tick()
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

