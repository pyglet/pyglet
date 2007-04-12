#!/usr/bin/env python

'''Test that resize event works correctly.

Expected behaviour:
    One window will be opened.  Resize the window and ensure that the
    dimensions printed to the terminal are correct.  You should see
    a green border inside the window but no red.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window

import window_util

class EVENT_RESIZE(unittest.TestCase):
    def on_resize(self, width, height):
        print 'Window resized to %dx%d.' % (width, height)

    def test_resize(self):
        w = window.Window(200, 200, resizable=True)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
            window_util.draw_client_border(w)
            w.flip()
        w.close()

if __name__ == '__main__':
    unittest.main()
