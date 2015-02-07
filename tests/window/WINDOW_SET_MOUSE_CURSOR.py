#!/usr/bin/env python

'''Test that image mouse cursor can be set.

Expected behaviour:
    One window will be opened.  The mouse cursor in the window will be
    a custom cursor.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.gl import *
from pyglet import image
from pyglet import window

from os.path import join, dirname
cursor_file = join(dirname(__file__), 'cursor.png')

class WINDOW_SET_MOUSE_CURSOR(unittest.TestCase):
    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_mouse_cursor(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height)
        img = image.load(cursor_file)
        w.set_mouse_cursor(window.ImageMouseCursor(img, 4, 28))
        w.push_handlers(self)
        glClearColor(1, 1, 1, 1)
        while not w.has_exit:
            glClear(GL_COLOR_BUFFER_BIT)
            w.flip()
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
