#!/usr/bin/env python
'''Test that a window can be opened.

Expected behaviour: 
    One small window will be opened coloured purple.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.window import *
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *

class WINDOW_OPEN(unittest.TestCase):
    def open_window(self):
        w = Window(200, 200)
        w.push_handlers(self.exit_handler)
        return w

    def draw_window(self, window, colour):
        window.switch_to()
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        window.flip()

    def test_open_window(self):
        self.exit_handler = ExitHandler()
        w1 = self.open_window()
        while not self.exit_handler.exit:
            self.draw_window(w1, (1, 0, 1, 1))
            w1.dispatch_events()
        w1.close()

if __name__ == '__main__':
    unittest.main()

