#!/usr/bin/env python

'''Base class for layout tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import sys

from pyglet.gl import *
from layout import *
from pyglet.window import *
from pyglet.window.event import *

class LayoutTestBase(unittest.TestCase):
    # Supply either XHTML or HTML.
    xhtml = None
    html = None

    def on_expose(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        self.layout.draw()
        self.window.flip()

    def test_main(self):
        width, height = 800, 600
        self.window = w = Window(width, height, visible=False)
        w.push_handlers(self)

        self.layout = Layout()
        w.push_handlers(self.layout)
        if self.xhtml:
            self.layout.set_xhtml(self.xhtml)
        else:
            self.layout.set_html(self.html)

        w.set_visible()
        while not w.has_exit:
            w.dispatch_events()
            self.on_expose()
        w.close()

if __name__ == '__main__':
    unittest.main()
