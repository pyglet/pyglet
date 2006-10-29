#!/usr/bin/env python

'''Test that mouse enter and leave events work correctly.

Expected behaviour:
    One window will be opened.  Move the mouse in and out of this window
    and ensure the events displayed are correct.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_MOUSE_ENTER_LEAVE(unittest.TestCase):
    def on_enter(self, x, y):
        print 'Entered at %f, %f' % (x, y)

    def on_leave(self, x, y):
        print 'Left at %f, %f' % (x, y)

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
