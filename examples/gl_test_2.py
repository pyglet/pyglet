#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: gl_test_2.py 111 2006-10-20 06:39:12Z r1chardj0n3s $'

import pyglet.window
from pyglet.window.event import *
import time

from pyglet.gl import *
from pyglet import clock


def setup():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., 1., 1., 100.)

    glMatrixMode(GL_MODELVIEW)
    glClearColor(1, 1, 1, 1)
    glColor4f(.5, .5, .5, .5)

def draw():
    global r
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

w1 = pyglet.window.Window(200, 200)
w1.switch_to()
setup()

c = clock.Clock(60)
w2 = pyglet.window.Window(400, 400)
w2.switch_to()
setup()


r = 0
while not (w1.has_exit or w2.has_exit):
    c.tick()

    w1.switch_to()
    w1.dispatch_events()
    draw()
    w1.flip()

    w2.switch_to()
    w2.dispatch_events()
    draw()
    w2.flip()
