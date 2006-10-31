#!/usr/bin/env python

'''Test that window expose event works correctly.

Expected behaviour:
    One window will be opened.  Uncovering the window from other windows
    or the edge of the screen should produce the expose event.

    Note that on OS X and other compositing window managers this event
    is equivalent to EVENT_SHOW.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_EXPOSE(unittest.TestCase):
    def on_expose(self):
        print 'Window exposed.'

    def test_expose(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(exit_handler)
        w.push_handlers(self)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
