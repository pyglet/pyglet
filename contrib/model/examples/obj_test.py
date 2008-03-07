#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: obj_test.py 111 2006-10-20 06:39:12Z r1chardj0n3s $'

import sys
import os
import ctypes
import pyglet

from pyglet.gl import *
from model import obj, geometric

w = pyglet.window.Window()

fourfv = ctypes.c_float * 4
glLightfv(GL_LIGHT0, GL_POSITION, fourfv(10, 20, 20, 0))
glLightfv(GL_LIGHT0, GL_AMBIENT, fourfv(0.2, 0.2, 0.2, 1.0))
glLightfv(GL_LIGHT0, GL_DIFFUSE, fourfv(0.8, 0.8, 0.8, 1.0))
glEnable(GL_LIGHT0)
glEnable(GL_LIGHTING)
glEnable(GL_DEPTH_TEST)

@w.event
def on_resize(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., float(width)/height, 1., 100.)
    glMatrixMode(GL_MODELVIEW)
    return True

@w.event
def on_draw():
    w.clear()
    glLoadIdentity()
    gluLookAt(0, 3, 3, 0, 0, 0, 0, 1, 0)
    glRotatef(r, 0, 1, 0)
    glRotatef(r/2, 1, 0, 0)
    bunny.draw()
    w.flip()

r = 0
def update(dt):
    global r
    r += 90*dt
    if r > 720: r = 0
pyglet.clock.schedule(update)

if len(sys.argv) == 1:
    objfile = os.path.join(os.path.split(__file__)[0], 'rabbit.obj')
else:
    objfile = sys.argv[1]

bunny = obj.OBJ(objfile)

pyglet.app.run()
