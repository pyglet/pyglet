#!/usr/bin/env python

'''Test that mouse button events work correctly.

Expected behaviour:
    One window will be opened.  Click within this window and check the console
    output for mouse events.  
     - Buttons 1, 2, 3 correspond to left, right middle
     - No events for scroll wheel
     - Modifiers are correct

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_BUTTON(unittest.TestCase):
    def on_mouse_press(self, button, x, y, modifiers):
        print 'Mouse button %d pressed at %f,%f with %s' % \
            (button, x, y, pyglet.window.event._modifiers_to_string(modifiers))

    def on_mouse_release(self, button, x, y, modifiers):
        print 'Mouse button %d released at %f,%f with %s' % \
            (button, x, y, pyglet.window.event._modifiers_to_string(modifiers))

    def test_button(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
