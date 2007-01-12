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

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.event import _symbol_to_string, _modifiers_to_string

class EVENT_KEYPRESS(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        print 'Pressed %s with modifiers %s' % \
            (pyglet.window.event._symbol_to_string(symbol),
             pyglet.window.event._modifiers_to_string(modifiers))

    def on_key_release(self, symbol, modifiers):
        print 'Released %s with modifiers %s' % \
            (pyglet.window.event._symbol_to_string(symbol),
             pyglet.window.event._modifiers_to_string(modifiers))

    def test_keypress(self):
        w = Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
