#!/usr/bin/env python

'''Test that mouse cursor can be set to a platform-dependent image.

Expected behaviour:
    One window will be opened. Press a key to change the cursor:

      d: default
      c: crosshair
      t: text
      w: wait

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: WINDOW_SET_MOUSE_VISIBLE.py 703 2007-02-28 14:18:00Z Alex.Holkner $'

import unittest

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *

class WINDOW_SET_MOUSE_PLATFORM_CURSOR(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        names = {
            K_D: CURSOR_DEFAULT,
            K_C: CURSOR_CROSSHAIR,
            K_T: CURSOR_TEXT,
            K_W: CURSOR_WAIT
        }
        if symbol in names:
            cursor = self.w.get_system_mouse_cursor(names[symbol])
            self.w.set_mouse_cursor(cursor)
            print 'Set cursor to "%s"' % names[symbol]
            
        return True

    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_visible(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
