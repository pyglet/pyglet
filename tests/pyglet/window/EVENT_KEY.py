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

import pyglet.window
from pyglet.window.event import *

class EVENT_KEYPRESS(unittest.TestCase):
    def on_keypress(self, symbol, modifiers):
        print 'Pressed %s with modifiers %s' % \
            (pyglet.window.event._symbol_to_string(symbol),
             pyglet.window.event._modifiers_to_string(modifiers))

    def on_keyrelease(self, symbol, modifiers):
        print 'Released %s with modifiers %s' % \
            (pyglet.window.event._symbol_to_string(symbol),
             pyglet.window.event._modifiers_to_string(modifiers))

    def test_keypress(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
