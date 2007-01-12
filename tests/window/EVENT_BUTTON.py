#!/usr/bin/env python

'''Test that mouse button events work correctly.

Expected behaviour:
    One window will be opened.  Click within this window and check the console
    output for mouse events.  
     - Buttons 1, 2, 4 correspond to left, middle, right, respectively.
     - No events for scroll wheel
     - Modifiers are correct

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.window import *
from pyglet.window.event import *

class EVENT_BUTTON(unittest.TestCase):
    def on_mouse_press(self, button, x, y, modifiers):
        print 'Mouse button %d pressed at %f,%f with %s' % \
            (button, x, y, pyglet.window.event._modifiers_to_string(modifiers))

    def on_mouse_release(self, button, x, y, modifiers):
        print 'Mouse button %d released at %f,%f with %s' % \
            (button, x, y, pyglet.window.event._modifiers_to_string(modifiers))

    def test_button(self):
        w = Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
