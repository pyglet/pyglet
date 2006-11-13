#!/usr/bin/env python

'''Test that the checkerboard pattern looks correct.

One window will open, it should show one instance of the checkerboard
pattern in two levels of grey.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.GL.VERSION_1_1 import *
import pyglet.image
import pyglet.window
import pyglet.window.event

class TEST_CHECKERBOARD(unittest.TestCase):
    def on_resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def on_expose(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        self.texture.draw()
        self.window.flip()

    def test_main(self):
        width, height = 200, 200
        self.window = w = pyglet.window.create(width, height, visible=False)
        exit_handler = pyglet.window.event.ExitHandler()
        w.push_handlers(exit_handler)
        w.push_handlers(self)

        self.texture = \
            pyglet.image.Image.create_checkerboard(width).get_texture()

        w.set_visible()
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
