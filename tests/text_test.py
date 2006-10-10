import sys
import os
import time

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet.text import Font

from ctypes import *

factory = pyglet.window.WindowFactory()
factory.config._attributes['doublebuffer'] = 1
w1 = factory.create(width=400, height=200)

filename = os.path.join(os.path.split(__file__)[0], 'Vera.ttf')
font = Font.load_font(filename, 72)
text = font.render('Hello World!')

exit_handler = ExitHandler()
w1.push_handlers(exit_handler)

c = clock.Clock()

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, w1.width, 0, w1.height, -1, 1)
glEnable(GL_COLOR_MATERIAL)

glMatrixMode(GL_MODELVIEW)
glClearColor(0, 0, 0, 0)
glColor4f(1, 1, 1, 1)
r = 0
while not exit_handler.exit:
    c.set_fps(60)
    w1.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    #r += 1
    if r > 360: r = 0
    glTranslatef(w1.width/2, w1.height/2, 0)
    glRotatef(r, 0, 0, 1)
    glTranslatef(-text.width/2, -text.height/2, 0)
    text.draw()

    w1.flip()

