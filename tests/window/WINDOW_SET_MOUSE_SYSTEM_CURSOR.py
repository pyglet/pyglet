#!/usr/bin/env python

'''Test that mouse cursor can be set to a platform-dependent image.

Expected behaviour:
    One window will be opened.  Press the left and right arrow keys to cycle
    through the system mouse cursors.  The current cursor selected will
    be printed to the terminal.

    Note that not all cursors are unique on each platform; for example,
    if a platform doesn't define a cursor for a given name, a suitable
    replacement (e.g., a plain arrow) will be used instead.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: WINDOW_SET_MOUSE_VISIBLE.py 703 2007-02-28 14:18:00Z Alex.Holkner $'

import unittest

from pyglet import window
from pyglet.window import key
from pyglet.gl import *

class WINDOW_SET_MOUSE_PLATFORM_CURSOR(unittest.TestCase):
    i = 0
    def on_key_press(self, symbol, modifiers):
        names = [
            window.CURSOR_DEFAULT,
            window.CURSOR_CROSSHAIR,
            window.CURSOR_HAND,
            window.CURSOR_HELP,
            window.CURSOR_NO,
            window.CURSOR_SIZE,
            window.CURSOR_SIZE_UP,
            window.CURSOR_SIZE_UP_RIGHT,
            window.CURSOR_SIZE_RIGHT,
            window.CURSOR_SIZE_DOWN_RIGHT,
            window.CURSOR_SIZE_DOWN,
            window.CURSOR_SIZE_DOWN_LEFT,
            window.CURSOR_SIZE_LEFT,
            window.CURSOR_SIZE_UP_LEFT,
            window.CURSOR_SIZE_UP_DOWN,
            window.CURSOR_SIZE_LEFT_RIGHT,
            window.CURSOR_TEXT,
            window.CURSOR_WAIT,
            window.CURSOR_WAIT_ARROW,
        ]
        if symbol == key.RIGHT:
            self.i = (self.i + 1) % len(names)
        elif symbol == key.LEFT:
            self.i = (self.i - 1) % len(names)
        cursor = self.w.get_system_mouse_cursor(names[self.i])
        self.w.set_mouse_cursor(cursor)
        print 'Set cursor to "%s"' % names[self.i]
            
        return True

    def test_set_visible(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height)
        w.push_handlers(self)
        while not w.has_exit:
            glClear(GL_COLOR_BUFFER_BIT)
            w.dispatch_events()
            w.flip()
        w.close()

if __name__ == '__main__':
    unittest.main()
