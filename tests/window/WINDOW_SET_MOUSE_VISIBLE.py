#!/usr/bin/env python

'''Test that mouse cursor can be made visible and hidden.

Expected behaviour:
    One window will be opened.  Press 'v' to hide mouse cursor and 'V' to
    show mouse cursor.  It should only affect the mouse when within the
    client area of the window.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet import window
from pyglet.window import key

class WINDOW_SET_MOUSE_VISIBLE(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        if symbol == key.V:
            visible = (modifiers & key.MOD_SHIFT)
            self.w.set_mouse_visible(visible)
            print 'Mouse is now %s' % (visible and 'visible' or 'hidden')

    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_visible(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
