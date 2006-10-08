import sys
import os
import time

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet.image import Texture, Image
from pyglet import freetype2

from ctypes import *

factory = pyglet.window.WindowFactory()
factory.config._attributes['doublebuffer'] = 1
w1 = factory.create(width=200, height=200)

filename = os.path.join(os.path.split(__file__)[0], 'Vera.ttf')
f = freetype2.load_face(filename, 16)
image = freetype2.render_char(f, 'A')
tex = Texture.from_image(image)

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
glEnable(GL_COLOR_MATERIAL)
glDisable(GL_BLEND)

glMatrixMode(GL_MODELVIEW)
glClearColor(0, 0, 0, 0)
glColor4f(1, 1, 1, 1)
r = 0
while exit_handler.running:
    c.set_fps(60)
    w1.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    r += 1
    if r > 360: r = 0
    glRotatef(r, 0, 0, 1)
    s = max(image.width, image.height) * 2
    glScalef(1./s, 1./s, 1.)
    glTranslatef(-tex.width/2, -tex.height/2, -1.)
    tex.draw()

    w1.flip()

