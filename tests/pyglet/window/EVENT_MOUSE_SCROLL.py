#!/usr/bin/env python

'''Test that mouse scroll event works correctly.

Expected behaviour:
    One window will be opened.  Move the scroll wheel and check that events
    are printed to console.  Positive values are associated with scrolling
    up.

    Scrolling can also be side-to-side, for example with an Apple Mighty
    Mouse.

    The actual scroll value is dependent on your operating system
    user preferences.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_MOUSE_SCROLL(unittest.TestCase):
    def on_mouse_scroll(self, dx, dy):
        print 'Mouse scrolled (%f, %f)' % (dx, dy)

    def test_mouse_scroll(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
