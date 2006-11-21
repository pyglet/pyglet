#!/usr/bin/env python

'''Base class for image tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import StringIO
from os.path import dirname, join

from pyglet.GL.VERSION_1_1 import *
import pyglet.image
import pyglet.window
import pyglet.window.event

class TestSave(unittest.TestCase):
    texture_file = None
    original_texture = None
    saved_texture = None
    show_checkerboard = True
    alpha = True

    def on_resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def on_expose(self):
        self.draw()
        self.window.flip()

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
            self.checkerboard.draw()
            glMatrixMode(GL_TEXTURE)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()

        self.draw_original()
        self.draw_saved()
            
    def draw_original(self):
        if self.original_texture:
            glPushMatrix()
            glTranslatef(
                self.window.width / 4 - self.original_texture.width / 2,
                (self.window.height - self.original_texture.height) / 2, 0)
            self.original_texture.draw()
            glPopMatrix()

    def draw_saved(self):
        if self.saved_texture:
            glPushMatrix()
            glTranslatef(
                self.window.width * 3 / 4 - self.saved_texture.width / 2,
                (self.window.height - self.saved_texture.height) / 2, 0)
            self.saved_texture.draw()
            glPopMatrix()

    def load_texture(self):
        if self.texture_file:
            self.texture_file = join(dirname(__file__), self.texture_file)
            self.original_texture = \
                pyglet.image.Texture.load(self.texture_file)

            file = StringIO.StringIO()
            self.original_texture.save(self.texture_file, file)
            file.seek(0)
            self.saved_texture = \
                pyglet.image.Texture.load(self.texture_file, file)

    def create_window(self):
        width, height = 400, 400
        return pyglet.window.create(width, height, visible=False)

    def test_save(self):
        self.window = w = self.create_window()
        exit_handler = pyglet.window.event.ExitHandler()
        w.push_handlers(exit_handler)
        w.push_handlers(self)

        self.checkerboard = \
            pyglet.image.Image.create_checkerboard(32).texture()

        self.load_texture()

        if self.alpha:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        w.set_visible()
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
