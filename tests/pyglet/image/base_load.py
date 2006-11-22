#!/usr/bin/env python

'''Base class for image tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
from os.path import dirname, join

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *
from pyglet.window import *
from pyglet.window.event import *

class TestLoad(unittest.TestCase):
    texture_file = None
    texture = None
    show_checkerboard = True
    alpha = True

    def on_resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def on_expose(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        if self.show_checkerboard:
            glPushMatrix()
            glScalef(self.window.width/float(self.checkerboard.width),
                     self.window.height/float(self.checkerboard.height),
                     1.)
            glMatrixMode(GL_TEXTURE)
            glPushMatrix()
            glScalef(self.window.width/float(self.checkerboard.width),
                     self.window.height/float(self.checkerboard.height),
                     1.)
            glMatrixMode(GL_MODELVIEW)
            self.checkerboard.draw()
            glMatrixMode(GL_TEXTURE)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()

        if self.texture:
            glPushMatrix()
            glTranslatef((self.window.width - self.texture.width) / 2,
                         (self.window.height - self.texture.height) / 2,
                         0)
            self.texture.draw()
            glPopMatrix()
        self.window.flip()

    def choose_codecs(self):
        pass

    def test_load(self):
        width, height = 400, 400
        self.window = w = Window(width, height, visible=False)
        self.choose_codecs()
        exit_handler = ExitHandler()
        w.push_handlers(exit_handler)
        w.push_handlers(self)

        self.checkerboard = \
            Image.create_checkerboard(32).texture()

        if self.texture_file:
            self.texture_file = join(dirname(__file__), self.texture_file)
            self.texture = \
                Texture.load(self.texture_file)

        if self.alpha:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        w.set_visible()
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
