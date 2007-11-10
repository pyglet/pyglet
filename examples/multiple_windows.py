#!/usr/bin/env python

'''Demonstrates how to manage OpenGL calls between two independent windows.
'''

from pyglet.gl import *
from pyglet import window
from pyglet import clock

def on_resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., width / float(height), 1., 100.)
    glMatrixMode(GL_MODELVIEW)

def setup():
    glClearColor(1, 1, 1, 1)
    glColor3f(.5, .5, .5)

def draw():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0, -5)
    glRotatef(r, 0, 0, 1)
    glRectf(-1, -1, 1, 1)

w1 = window.Window(200, 200, caption='First window', resizable=True)
w1.on_resize = on_resize
w1.switch_to()
setup()

w2 = window.Window(300, 300, caption='Second window', resizable=True)
w2.on_resize = on_resize
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
