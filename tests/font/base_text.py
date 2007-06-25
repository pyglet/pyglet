#!/usr/bin/env python

'''Base class for text tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import sys

from pyglet.gl import *
from pyglet import font
from pyglet.window import *
from pyglet.window.event import *

from tests.regression import ImageRegressionTestCase

class TextTestBase(ImageRegressionTestCase):
    font_name = ''
    font_size = 24
    text = 'Quickly brown fox'
    window_size = 200, 200

    def on_expose(self):
        glClearColor(0.5, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        self.draw()
        self.window.flip()

        if self.capture_regression_image():
            self.window.exit_handler.has_exit = True

    def render(self):
        fnt = font.load(self.font_name, self.font_size) 
        self.label = font.Text(fnt, self.text, 10, 10)

    def draw(self):
        self.label.draw()

    def test_main(self):
        width, height = self.window_size
        self.window = w = Window(width, height, visible=False, resizable=True)
        w.push_handlers(self)

        self.render()

        w.set_visible()
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
