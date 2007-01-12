#!/usr/bin/env python

'''Test that window size can be set.

Expected behaviour:
    One window will be opened.  The window's dimensions will be printed
    to the terminal.  

     - press "x" to increase the width
     - press "X" to decrease the width
     - press "y" to increase the height
     - press "Y" to decrease the height

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *

class WINDOW_SET_SIZE(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        delta = 20
        if modifiers & MOD_SHIFT:
            delta = -delta
        if symbol == K_X:
            self.width += delta
        elif symbol == K_Y:
            self.height += delta
        self.w.set_size(self.width, self.height)
        print 'Window size set to %dx%d.' % (self.width, self.height)

    def test_set_size(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
