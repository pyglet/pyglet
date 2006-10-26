#!/usr/bin/env python
'''Test that multiple windows can be opened.

Expected behaviour: 
    Two small windows will be opened, one coloured yellow and the other
    purple.

Interaction:
    Close either window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *

class MULTIPLE_WINDOW_OPEN(unittest.TestCase):

    def open_window(self, colour):
        w = pyglet.window.create(200, 200)
        w.push_handlers(self.exit_handler)
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        w.flip()
        return w

    def test_open_window(self):
        self.exit_handler = ExitHandler()
        w1 = self.open_window((1, 0, 1, 1))
        w2 = self.open_window((1, 1, 0, 1))
        while not self.exit_handler.exit:
            w1.dispatch_events()
            w2.dispatch_events()
        w1.close()
        w2.close()

if __name__ == '__main__':
    unittest.main()

