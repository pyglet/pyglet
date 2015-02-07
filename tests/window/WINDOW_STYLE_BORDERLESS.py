#!/usr/bin/env python

'''Test that window style can be borderless.

Expected behaviour:
    One borderless window will be opened.

    Mouse click in the window to close it and end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: WINDOW_SET_MOUSE_CURSOR.py 717 2007-03-03 07:04:10Z Alex.Holkner $'

import unittest

from pyglet.gl import *
from pyglet import window
from pyglet.window import key

class WINDOW_TEST_STYLE_BORDERLESS(unittest.TestCase):
    def test_style_borderless(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height, 
                                   style=window.Window.WINDOW_STYLE_BORDERLESS)
        @w.event
        def on_mouse_press(*args): w.has_exit = True

        glClearColor(1, 1, 1, 1)
        while not w.has_exit:
            glClear(GL_COLOR_BUFFER_BIT)
            w.flip()
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
