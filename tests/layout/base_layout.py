#!/usr/bin/env python

'''Base class for layout tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import sys

from pyglet.GL.VERSION_1_1 import *
from pyglet.layout import *
from pyglet.text import *
from pyglet.window import *
from pyglet.window.event import *

class LayoutTestBase(unittest.TestCase):
    xhtml = '''<?xml version="1.0"?>
    <html>
      <body>
        <p>Test base.</p>
      </body>
    </html>
    '''

    offset_top = 0

    def on_resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        self.layout.render_device.width = width
        self.layout.render_device.height = height
        self.layout.layout()

        # XXX HACK
        self.layout_height = int(self.layout.frame.children[-1].border_bottom)

    def on_mouse_scroll(self, dx, dy):
        self.offset_top -= dy * 30
        self.on_expose()

    def on_expose(self):
        self.offset_top = max(min(self.offset_top, 
                                  self.layout_height - self.window.height), 0)

        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, self.window.height + self.offset_top, 0)
        self.layout.draw()
        self.window.flip()

    def test_main(self):
        width, height = 800, 600
        self.window = w = Window(width, height, visible=False)
        self.exit_handler = ExitHandler()
        w.push_handlers(self.exit_handler)
        w.push_handlers(self)

        self.layout = render_xhtml(self.xhtml)

        w.set_visible()
        while not self.exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
