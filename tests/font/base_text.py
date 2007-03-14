#!/usr/bin/env python

'''Base class for text tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import sys

from pyglet.gl import *
from pyglet.ext.scene2d.textsprite import *
from pyglet.font import *
from pyglet.window import *
from pyglet.window.event import *

from tests.regression import ImageRegressionTestCase

class TextTestBase(ImageRegressionTestCase):
    font_name = ''
    font_size = 24
    text = 'Quickly brown fox'

    def on_expose(self):
        glClearColor(0.5, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(10, 10, 0)
        self.sprite.draw()
        self.window.flip()

        if self.capture_regression_image():
            self.window.exit_handler.has_exit = True

    def create_font(self):
        self.font = load_font(self.font_name, self.font_size) 

    def render(self):
        self.sprite = TextSprite(self.font, self.text)

    def test_main(self):
        width, height = 200, 200
        self.window = w = Window(width, height, visible=False)
        w.push_handlers(self)

        self.create_font()
        self.render()

        w.set_visible()
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
