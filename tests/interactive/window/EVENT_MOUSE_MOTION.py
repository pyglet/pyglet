#!/usr/bin/env python

'''Test that mouse motion event works correctly.

Expected behaviour:
    One window will be opened.  Move the mouse in and out of this window
    and ensure the absolute and relative coordinates are correct.
     - Absolute coordinates should have (0,0) at bottom-left of client area
       of window with positive y-axis pointing up and positive x-axis right.
     - Relative coordinates should be positive when moving up and right.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window

class EVENT_MOUSEMOTION(unittest.TestCase):
    def on_mouse_motion(self, x, y, dx, dy):
        print 'Mouse at (%f, %f); relative (%f, %f).' % \
            (x, y, dx, dy)

    def test_motion(self):
        w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
