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

from pyglet import window
from pyglet import event
w = None

class EVENT_CLOSE(unittest.TestCase):
    def on_close(self):
        print 'Window close event.'
        return event.EVENT_HANDLED

    def on_key_press(self, symbol, mods):
        if symbol == window.key.ESCAPE:
            global w
            super(window.Window, w).on_close()

    def test_close(self):
        global w
        w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()
        
if __name__ == '__main__':
    unittest.main()
