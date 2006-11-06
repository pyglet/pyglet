#!/usr/bin/env python

'''Test that window location can be set.

Expected behaviour:
    One window will be opened.  The window's location will be printed
    to the terminal.  

     - Use the arrow keys to move the window.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *
from pyglet.window.key import *

class WINDOW_SET_SIZE(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        x, y = self.w.get_location()
        if symbol == K_LEFT:
            x -= 10
        if symbol == K_RIGHT:
            x += 10
        if symbol == K_UP:
            y -= 10
        if symbol == K_DOWN:
            y += 10
        self.w.set_location(x, y)
        print 'Window location set to %dx%d.' % (x, y)

    def test_set_size(self):
        self.w = w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
