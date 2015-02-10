#!/usr/bin/env python

'''Test that minimum and maximum window size can be set.

Expected behaviour:
    One window will be opened.  The window's dimensions will be printed
    to the terminal.  Initially the window has no minimum or maximum
    size (besides any OS-enforced limit).

     - press "n" to set the minimum size to be the current size.
     - press "x" to set the maximum size to be the current size.

    You should see a green border inside the window but no red.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.window import key

import window_util

class WINDOW_SET_MIN_MAX_SIZE(unittest.TestCase):
    def on_resize(self, width, height):
        print 'Window size is %dx%d.' % (width, height)
        self.width, self.height = width, height

    def on_key_press(self, symbol, modifiers):
        if symbol == key.N:
            self.w.set_minimum_size(self.width, self.height)
            print 'Minimum size set to %dx%d.' % (self.width, self.height)
        elif symbol == key.X:
            self.w.set_maximum_size(self.width, self.height)
            print 'Maximum size set to %dx%d.' % (self.width, self.height)

    def test_min_max_size(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height, resizable=True)
        w.push_handlers(self)
        while not w.has_exit:
            window_util.draw_client_border(w)
            w.flip()
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
