import sys
import os

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet.image import Image, Texture

from ctypes import *

if len(sys.argv) != 2:
    print 'Usage: %s <PNG/JPEG filename>'%sys.argv[0]
    sys.exit()

window = pyglet.window.Window(width=200, height=200)

tex = Texture.load(sys.argv[1])

exit_handler = ExitHandler()
window.push_handlers(exit_handler)

c = clock.Clock()

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
while not exit_handler.exit:
    c.set_fps(60)
    window.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    r += 1
    if r > 360: r = 0
    glRotatef(r, 0, 0, 1)
    s = max(tex.width, tex.height)
    glScalef(1./s, 1./s, 1.)
    glTranslatef(-tex.width/2, -tex.height/2, -1.)
    tex.draw()

    window.flip()

