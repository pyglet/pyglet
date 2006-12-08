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

from pyglet.window import *
from pyglet.window.event import *

class EVENT_MOVE(unittest.TestCase):
    def on_move(self, x, y):
        print 'Window moved to %dx%d.' % (x, y)

    def test_move(self):
        w = Window(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
