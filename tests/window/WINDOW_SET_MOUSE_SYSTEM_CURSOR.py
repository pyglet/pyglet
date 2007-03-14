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

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window import key
from pyglet.gl import *

class WINDOW_SET_MOUSE_PLATFORM_CURSOR(unittest.TestCase):
    i = 0
    def on_key_press(self, symbol, modifiers):
        names = [
            CURSOR_DEFAULT,
            CURSOR_CROSSHAIR,
            CURSOR_HAND,
            CURSOR_HELP,
            CURSOR_NO,
            CURSOR_SIZE,
            CURSOR_SIZE_UP,
            CURSOR_SIZE_UP_RIGHT,
            CURSOR_SIZE_RIGHT,
            CURSOR_SIZE_DOWN_RIGHT,
            CURSOR_SIZE_DOWN,
            CURSOR_SIZE_DOWN_LEFT,
            CURSOR_SIZE_LEFT,
            CURSOR_SIZE_UP_LEFT,
            CURSOR_SIZE_UP_DOWN,
            CURSOR_SIZE_LEFT_RIGHT,
            CURSOR_TEXT,
            CURSOR_WAIT,
            CURSOR_WAIT_ARROW,
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
        self.w = w = Window(self.width, self.height)
        w.push_handlers(self)
        while not w.has_exit:
            glClear(GL_COLOR_BUFFER_BIT)
            w.dispatch_events()
            w.flip()
        w.close()

if __name__ == '__main__':
    unittest.main()
