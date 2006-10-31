#!/usr/bin/env python

'''Test that show and hide events work correctly.

Expected behaviour:
    One window will be opened.  There should be one shown event printed
    initially.  Minimizing and restoring the window should produce hidden
    and shown events, respectively.

    On OS X the events should also be fired when the window is hidden
    and shown (using Command+H or the dock context menu).
    
    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_SHOW_HIDE(unittest.TestCase):
    def on_show(self):
        print 'Window shown.'

    def on_hide(self):
        print 'Window hidden.'

    def test_show_hide(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(exit_handler)
        w.push_handlers(self)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
