#!/usr/bin/env python

'''Test that window move event works correctly.

Expected behaviour:
    One window will be opened.  Move the window and ensure that the
    location printed to the terminal is correct.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window

class EVENT_MOVE(unittest.TestCase):
    def on_move(self, x, y):
        print 'Window moved to %dx%d.' % (x, y)

    def test_move(self):
        w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
