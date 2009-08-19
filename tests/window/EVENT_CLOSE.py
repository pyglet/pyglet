#!/usr/bin/env python

'''Test that close event works correctly.

Expected behaviour:
    One window will be opened.  Click the close button and ensure the
    event is printed to the terminal.  The window should not close
    when you do this.

    Click Left mouse button to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet import event

class EVENT_CLOSE(unittest.TestCase):
    def on_close(self):
        print 'Window close event.'
        return event.EVENT_HANDLED

    def on_mouse_press(self, x, y, button, modifiers):
        super(window.Window, self.w).on_close()

    def test_close(self):
        self.w = window.Window(200, 200)
        self.w.push_handlers(self)
        while not self.w.has_exit:
            self.w.dispatch_events()
        self.w.close()
        
if __name__ == '__main__':
    unittest.main()
