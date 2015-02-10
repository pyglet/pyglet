#!/usr/bin/env python

'''Test that window can be minimized and maximized.

Expected behaviour:
    One window will be opened.

     - press "x" to maximize the window.
     - press "n" to minimize the window.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.window import key

class WINDOW_MINIMIZE_MAXIMIZE(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        if symbol == key.X:
            self.w.maximize()
            print 'Window maximized.'
        elif symbol == key.N:
            self.w.minimize()
            print 'Window minimized.'

    def test_minimize_maximize(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height, resizable=True)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
