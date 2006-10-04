import sys
import os
import time

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet.image import png

from ctypes import *

factory = pyglet.window.WindowFactory()
factory.config._attributes['doublebuffer'] = 1
w1 = factory.create(width=200, height=200)

image = png.read(os.path.join(os.path.split(__file__)[0], 'kitten.png'))

if image.components == 3: tex_comps = GL_RGB
else: tex_comps = GL_RGBA

# Create the OpenGL texture
texid = c_uint(0)
glGenTextures(1, byref(texid))
glBindTexture(GL_TEXTURE_2D, texid)
glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)
glTexImage2D(GL_TEXTURE_2D, 0, image.components, image.width, image.height, 0,
    tex_comps, GL_UNSIGNED_BYTE, image.data)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

del image



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
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
glEnable(GL_COLOR_MATERIAL)
glDisable(GL_BLEND)
glPushAttrib(GL_ENABLE_BIT)
glEnable(GL_TEXTURE_2D)

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
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(-1., -1., -5.)
    glTexCoord2f(0, 1)
    glVertex3f(-1., 1., -5.)
    glTexCoord2f(1, 1)
    glVertex3f(1., 1., -5.)
    glTexCoord2f(1, 0)
    glVertex3f(1., -1., -5.)
    glEnd()

    w1.flip()

