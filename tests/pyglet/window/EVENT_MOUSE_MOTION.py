#!/usr/bin/env python

'''Test that mouse motion event works correctly.

Expected behaviour:
    One window will be opened.  Move the mouse in and out of this window
    and ensure the absolute and relative coordinates are correct.
     - Absolute coordinates relative to 0,0 at top-left of client area
       of window.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_MOUSEMOTION(unittest.TestCase):
    def on_mouse_motion(self, x, y, dx, dy):
        print 'Mouse at (%f, %f); relative (%f, %f).' % \
            (x, y, dx, dy)

    def test_motion(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
