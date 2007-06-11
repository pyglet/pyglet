#!/usr/bin/env python

'''Test that window size can be set.

Expected behaviour:
    One window will be opened.  The window's dimensions will be printed
    to the terminal.  

     - press "x" to increase the width
     - press "X" to decrease the width
     - press "y" to increase the height
     - press "Y" to decrease the height

    You should see a green border inside the window but no red.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.window import key

import window_util

class WINDOW_SET_SIZE(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        delta = 20
        if modifiers & key.MOD_SHIFT:
            delta = -delta
        if symbol == key.X:
            self.width += delta
        elif symbol == key.Y:
            self.height += delta
        self.w.set_size(self.width, self.height)
        print 'Window size set to %dx%d.' % (self.width, self.height)

    def test_set_size(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height, resizable=True)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
            window_util.draw_client_border(w)
            w.flip()
        w.close()

if __name__ == '__main__':
    unittest.main()
