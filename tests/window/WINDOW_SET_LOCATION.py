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

from pyglet import window
from pyglet.window import key

class WINDOW_SET_SIZE(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        x, y = self.w.get_location()
        if symbol == key.LEFT:
            x -= 10
        if symbol == key.RIGHT:
            x += 10
        if symbol == key.UP:
            y -= 10
        if symbol == key.DOWN:
            y += 10
        self.w.set_location(x, y)
        print 'Window location set to %dx%d.' % (x, y)

    def test_set_size(self):
        self.w = w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
