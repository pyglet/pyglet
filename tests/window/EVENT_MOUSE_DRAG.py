#!/usr/bin/env python

'''Test that mouse drag event works correctly.

Expected behaviour:
    One window will be opened.  Click and drag with the mouse and ensure
    that buttons, coordinates and modifiers are reported correctly.  Events
    should be generated even when the drag leaves the window.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet import window
from pyglet.window.event import WindowEventLogger

class EVENT_MOUSE_DRAG(unittest.TestCase):
    def test_mouse_drag(self):
        w = window.Window(200, 200)
        w.push_handlers(WindowEventLogger())
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
