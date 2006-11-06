#!/usr/bin/env python

'''Test that minimum and maximum window size can be set.

Expected behaviour:
    One window will be opened.  The window's dimensions will be printed
    to the terminal.  Initially the window has no minimum or maximum
    size (besides any OS-enforced limit).

     - press "n" to set the minimum size to be the current size.
     - press "x" to set the maximum size to be the current size.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *
from pyglet.window.key import *

class WINDOW_SET_MIN_MAX_SIZE(unittest.TestCase):
    def on_resize(self, width, height):
        print 'Window size is %dx%d.' % (width, height)
        self.width, self.height = width, height

    def on_key_press(self, symbol, modifiers):
        if symbol == K_N:
            self.w.set_minimum_size(self.width, self.height)
            print 'Minimum size set to %dx%d.' % (self.width, self.height)
        elif symbol == K_X:
            self.w.set_maximum_size(self.width, self.height)
            print 'Maximum size set to %dx%d.' % (self.width, self.height)

    def test_min_max_size(self):
        self.width, self.height = 200, 200
        self.w = w = pyglet.window.create(self.width, self.height)
        exit_handler = ExitHandler()
        w.push_handlers(exit_handler)
        w.push_handlers(self)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
