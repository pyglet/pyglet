#!/usr/bin/env python

'''Test that the checkerboard pattern looks correct.

One window will open, it should show one instance of the checkerboard
pattern in two levels of grey.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.gl import *
from pyglet import image
from pyglet.window import *
from pyglet.window.event import *

from tests.regression import ImageRegressionTestCase

class TEST_CHECKERBOARD(ImageRegressionTestCase):
    has_exit = False

    def on_expose(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        self.texture.blit(0, 0, 0)
        self.window.flip()

        if self.capture_regression_image():
            self.has_exit = True

    def test_main(self):
        width, height = 200, 200
        self.window = w = Window(width, height, visible=False)
        w.push_handlers(self)

        self.texture = image.create(32, 32, image.CheckerImagePattern()).texture

        w.set_visible()
        while not (w.has_exit or self.has_exit):
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
