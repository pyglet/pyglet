#!/usr/bin/env python

'''Test that exclusive mouse mode can be set.

Expected behaviour:
    One window will be opened.  Press 'e' to enable exclusive mode and 'E'
    to disable exclusive mode.

    In exclusive mode:
     - the mouse cursor should be invisible
     - moving the mouse should generate events with bogus x,y but correct
       dx and dy.
     - it should not be possible to switch applications with the mouse
     - if application loses focus (i.e., with keyboard), the mouse should
       operate normally again until focus is returned to the app, in which
       case it should hide again.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.window import key

class WINDOW_SET_EXCLUSIVE_MOUSE(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        if symbol == key.E:
            exclusive = not (modifiers & key.MOD_SHIFT)
            self.w.set_exclusive_mouse(exclusive)
            print 'Exclusive mouse is now %r' % exclusive

    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_exclusive_mouse(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
