#!/usr/bin/env python

'''Test that close event works correctly.

Expected behaviour:
    One window will be opened.  Click the close button and ensure the
    event is printed to the terminal.  The window should not close
    when you do this.

    Press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_CLOSE(unittest.TestCase):
    def on_close(self):
        print 'Window close event.'

    def test_close(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
