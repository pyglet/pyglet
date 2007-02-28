#!/usr/bin/env python

'''Test that exclusive mouse mode can be set.

Expected behaviour:
    One window will be opened.  The mouse cursor in the window will be
    a custom cursor.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.gl import *
from pyglet.image import load_image
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *

from os.path import join, dirname
cursor_file = join(dirname(__file__), 'cursor.png')

class WINDOW_SET_EXCLUSIVE_MOUSE(unittest.TestCase):
    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_exclusive_mouse(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        image = load_image(cursor_file)
        w.set_mouse_cursor(MouseCursor(image, 4, 28))
        w.push_handlers(self)
        glClearColor(1, 1, 1, 1)
        while not w.has_exit:
            glClear(GL_COLOR_BUFFER_BIT)
            w.dispatch_events()
            w.flip()
        w.close()

if __name__ == '__main__':
    unittest.main()
