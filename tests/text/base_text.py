#!/usr/bin/env python

'''Base class for text tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import sys

from pyglet.GL.VERSION_1_1 import *
from pyglet.scene2d.textsprite import *
from pyglet.text import *
from pyglet.window import *
from pyglet.window.event import *

from tests.regression import ImageRegressionTestCase

class TextTestBase(ImageRegressionTestCase):
    font_name = ''
    font_size = 24
    text = 'Quickly brown fox'

    def on_resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def on_expose(self):
        glClearColor(0.5, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(10, 10, 0)
        self.sprite.draw()
        self.window.flip()

        if self.capture_regression_image():
            self.exit_handler.exit = True

    def create_font(self):
        self.font = Font(self.font_name, self.font_size) 

    def render(self):
        self.sprite = TextSprite(self.font, self.text)

    def test_main(self):
        width, height = 200, 200
        self.window = w = Window(width, height, visible=False)
        self.exit_handler = ExitHandler()
        w.push_handlers(self.exit_handler)
        w.push_handlers(self)

        self.create_font()
        self.render()

        w.set_visible()
        while not self.exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
