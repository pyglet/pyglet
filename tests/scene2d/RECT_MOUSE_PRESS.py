#!/usr/bin/env python

'''Testing mouse press

Press the arrow keys to scroll the focus around the map (this will move the
map eventually.)

Press a mouse button on the map and check the cell printed to the console
matches the cell in the window.

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase
import pyglet.scene2d
from pyglet.scene2d.event import *
from pyglet.scene2d.debug import gen_rect_map

class RectFlatDebugTest(RenderBase):
    def test_main(self):
        self.init_window(256, 256)
        m = gen_rect_map([[{'val':'a'},{'val':'b'}]*10]*20, 32, 32)
        self.set_map(m)
        self.w.push_handlers(self.view)
        self.view.allow_oob = False

        @event(self.view)
        @for_cells([m], val='a')
        def on_mouse_press(objs, button, x, y, modifiers):
            print 'PRESSED', objs

        self.show_focus()
        self.run_test()

if __name__ == '__main__':
    unittest.main()
