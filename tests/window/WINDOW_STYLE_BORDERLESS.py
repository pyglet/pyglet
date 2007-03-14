#!/usr/bin/env python

'''Test that window style can be borderless.

Expected behaviour:
    One borderless window will be opened.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: WINDOW_SET_MOUSE_CURSOR.py 717 2007-03-03 07:04:10Z Alex.Holkner $'

import unittest

from pyglet.gl import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window import key

class WINDOW_TEST_STYLE_BORDERLESS(unittest.TestCase):
    def test_style_borderless(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height, 
                            style=WINDOW_STYLE_BORDERLESS)
        glClearColor(1, 1, 1, 1)
        while not w.has_exit:
            glClear(GL_COLOR_BUFFER_BIT)
            w.dispatch_events()
            w.flip()
        w.close()

if __name__ == '__main__':
    unittest.main()
