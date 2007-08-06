#!/usr/bin/env python

'''Displays a rotating square using OpenGL.
'''

from pyglet.gl import *
from pyglet import clock
from pyglet import window

w = window.Window(200, 200)

@w.event
def on_resize(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., 1., 1., 100.)

    glMatrixMode(GL_MODELVIEW)
    glClearColor(1, 1, 1, 1)
    glColor4f(.5, .5, .5, .5)

r = 0

clock.set_fps_limit(30)
while not w.has_exit:
    dt = clock.tick()
    r += dt * 30
    if r > 360: r = 0


    w.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    glRotatef(r, 0, 0, 1)
    glBegin(GL_QUADS)
    glVertex3f(-1., -1., -5.)
    glVertex3f(-1., 1., -5.)
    glVertex3f(1., 1., -5.)
    glVertex3f(1., -1., -5.)
    glEnd()

    w.flip()

