import sys
import os

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet.scene2d import Image2d

from ctypes import *

if len(sys.argv) != 2:
    print 'Usage: %s <PNG/JPEG filename>'%sys.argv[0]
    sys.exit()

window = pyglet.window.Window(width=400, height=400)

image = Image2d.load(sys.argv[1])

c = clock.Clock(60)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(60., 1., 1., 100.)
glEnable(GL_COLOR_MATERIAL)

glMatrixMode(GL_MODELVIEW)
glClearColor(0, 0, 0, 0)
glColor4f(1, 1, 1, 1)

glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_BLEND)

r = 0
while not window.has_exit:
    c.tick()
    window.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    r = (r + 1) % 360
    glRotatef(r, 0, 0, 1)
    s = max(image.width, image.height)
    glScalef(1./s, 1./s, 1.)
    glTranslatef(-image.width/2, -image.height/2, -1.)
    image.draw()

    window.flip()

