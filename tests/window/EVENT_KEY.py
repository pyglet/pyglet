#!/usr/bin/env python

'''Test that key press and release events work correctly.

Expected behaviour:
    One window will be opened.  Type into this window and check the console
    output for key press and release events.  Check that the correct
    key symbol and modifiers are reported.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.window import key

class EVENT_KEYPRESS(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        print 'Pressed %s with modifiers %s' % \
            (key.symbol_string(symbol), key.modifiers_string(modifiers))

    def on_key_release(self, symbol, modifiers):
        print 'Released %s with modifiers %s' % \
            (key.symbol_string(symbol), key.modifiers_string(modifiers))

    def test_keypress(self):
        w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
