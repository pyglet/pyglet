#!/usr/bin/env python

'''Base class for image tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
from os.path import dirname, join

from pyglet.gl import *
from pyglet import image
from pyglet.image import codecs
from pyglet.window import *
from pyglet.window.event import *

from tests.regression import ImageRegressionTestCase

class TestLoad(ImageRegressionTestCase):
    texture_file = None
    image = None
    texture = None
    show_checkerboard = True
    alpha = True
    has_exit = False
    decoder = None

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
            self.checkerboard.blit(0, 0, 0)
            glMatrixMode(GL_TEXTURE)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()

        if self.texture:
            glPushMatrix()
            glTranslatef((self.window.width - self.texture.width) / 2,
                         (self.window.height - self.texture.height) / 2,
                         0)
            self.texture.blit(0, 0, 0)
            glPopMatrix()
        self.window.flip()

        if self.capture_regression_image():
            self.has_exit = True

    def load_image(self):
        if self.texture_file:
            self.texture_file = join(dirname(__file__), self.texture_file)
            self.image = image.load(self.texture_file, decoder=self.decoder)

    def test_load(self):
        width, height = 800, 600
        self.window = w = Window(width, height, visible=False)
        w.push_handlers(self)

        self.screen = image.get_buffer_manager().get_color_buffer()
        self.checkerboard = image.create(32, 32, image.CheckerImagePattern())

        self.load_image()
        if self.image:
            self.texture = self.image.texture
    
        if self.alpha:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        w.set_visible()
        while not (w.has_exit or self.has_exit):
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
