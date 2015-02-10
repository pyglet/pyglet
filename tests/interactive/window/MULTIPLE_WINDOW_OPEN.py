#!/usr/bin/env python
'''Test that multiple windows can be opened.

Expected behaviour: 
    Two small windows will be opened, one coloured yellow and the other
    purple.

    Close either window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.gl import *

class MULTIPLE_WINDOW_OPEN(unittest.TestCase):
    def open_window(self):
        return window.Window(200, 200)

    def draw_window(self, window, colour):
        window.switch_to()
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        window.flip()

    def test_open_window(self):
        w1 = self.open_window()
        w2 = self.open_window()
        while not (w1.has_exit or w2.has_exit):
            self.draw_window(w1, (1, 0, 1, 1))
            self.draw_window(w2, (1, 1, 0, 1))
            w1.dispatch_events()
            w2.dispatch_events()
        w1.close()
        w2.close()

if __name__ == '__main__':
    unittest.main()

