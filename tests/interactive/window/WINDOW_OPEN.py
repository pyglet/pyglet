#!/usr/bin/env python
'''Test that a window can be opened.

Expected behaviour: 
    One small window will be opened coloured purple.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet import window
from pyglet.gl import *

class WINDOW_OPEN(unittest.TestCase):
    def open_window(self):
        return window.Window(200, 200)

    def draw_window(self, window, colour):
        window.switch_to()
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        window.flip()

    def test_open_window(self):
        w1 = self.open_window()
        while not w1.has_exit:
            self.draw_window(w1, (1, 0, 1, 1))
            w1.dispatch_events()
        w1.close()

if __name__ == '__main__':
    unittest.main()

