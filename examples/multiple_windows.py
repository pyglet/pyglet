#!/usr/bin/env python

'''Demonstrates how to manage OpenGL calls between two independent windows.
'''

from pyglet.gl import *
from pyglet import window
from pyglet import clock

def setup():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., 1., 1., 100.)

    glMatrixMode(GL_MODELVIEW)
    glClearColor(1, 1, 1, 1)
    glColor4f(.5, .5, .5, .5)

def draw():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    glRotatef(r, 0, 0, 1)
    glBegin(GL_QUADS)
    glVertex3f(-1., -1., -5.)
    glVertex3f(-1., 1., -5.)
    glVertex3f(1., 1., -5.)
    glVertex3f(1., -1., -5.)
    glEnd()

w1 = window.Window(200, 200, caption='First window')
w1.switch_to()
setup()

w2 = window.Window(300, 300, caption='Second window')
w2.switch_to()
setup()

r = 0
clock.set_fps_limit(30)
while not (w1.has_exit or w2.has_exit):
    dt = clock.tick()
    r += 1
    if r > 360: r = 0

    w1.switch_to()
    w1.dispatch_events()
    draw()
    w1.flip()

    w2.switch_to()
    w2.dispatch_events()
    draw()
    w2.flip()
