#!/usr/bin/env python

'''Testing flat map allow_oob enforcement.

Press 0-9 to set the size of the view in the window (1=10%, 0=100%)

Press arrow keys to move view focal point (little ball) around map.
Press "o" to turn allow_oob on and off.

You should see no black border with allow_oob=False.

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase
import scene2d
from pyglet.event import *
from pyglet.window.event import *
from pyglet.window import key
from scene2d.debug import gen_rect_map

class OOBTest(RenderBase):
    def test_main(self):
        self.init_window(256, 256)
        self.set_map(gen_rect_map([[{}]*10]*10, 32, 32))

        @event(self.w)
        def on_text(text):
            if text == 'o':
                self.view.allow_oob = not self.view.allow_oob
                print 'NOTE: allow_oob =', self.view.allow_oob
                return
            try:
                size = int(25.6 * float(text))
                if size == 0: size = 256
                c = self.view.camera
                c.width = c.height = size
                c.x = c.y = (256-size)/2
            except:
                return EVENT_UNHANDLED
        print 'NOTE: allow_oob =', self.view.allow_oob

        self.show_focus()

        self.run_test()
if __name__ == '__main__':
    unittest.main()
