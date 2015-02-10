#!/usr/bin/env python

'''Base class for image tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
from os.path import abspath, dirname, join

from pyglet.gl import *
from pyglet import image
from pyglet.image import codecs
from pyglet.window import *
from pyglet.window.event import *
from pyglet.compat import BytesIO

from tests.regression import ImageRegressionTestCase

test_data_path = abspath(join(dirname(__file__), '..', 'data', 'images'))

class TestSave(ImageRegressionTestCase):
    texture_file = None
    original_texture = None
    saved_texture = None
    show_checkerboard = True
    alpha = True
    has_exit = False

    def on_expose(self):
        self.draw()
        self.window.flip()

        if self.capture_regression_image():
            self.has_exit = True

    def draw(self):
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

        self.draw_original()
        self.draw_saved()
            
    def draw_original(self):
        if self.original_texture:
            self.original_texture.blit(
                self.window.width / 4 - self.original_texture.width / 2,
                (self.window.height - self.original_texture.height) / 2, 
                0)

    def draw_saved(self):
        if self.saved_texture:
            self.saved_texture.blit(
                self.window.width * 3 / 4 - self.saved_texture.width / 2,
                (self.window.height - self.saved_texture.height) / 2, 
                0)

    def load_texture(self):
        if self.texture_file:
            self.texture_file = join(test_data_path, self.texture_file)
            self.original_texture = image.load(self.texture_file).texture

            file = BytesIO()
            self.original_texture.save(self.texture_file, file,
                                       encoder=self.encoder)
            file.seek(0)
            self.saved_texture = image.load(self.texture_file, file).texture

    def create_window(self):
        width, height = 800, 600
        return Window(width, height, visible=False)

    def test_save(self):
        self.window = w = self.create_window()
        w.push_handlers(self)

        self.screen = image.get_buffer_manager().get_color_buffer()
        self.checkerboard = image.create(32, 32, image.CheckerImagePattern())

        self.load_texture()

        if self.alpha:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        w.set_visible()
        while not (w.has_exit or self.has_exit):
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
