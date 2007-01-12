#!/usr/bin/env python

'''Testing flat map scrolling.

Press arrow keys to move view focal point (red dot) around map.

You will be able to move "off" the map.

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase
import pyglet.scene2d
from pyglet.scene2d.debug import genmap

class HexFlatDebugTest(RenderBase):
    def test_main(self):
        m = gen_rect_map(['a'*10]*10, 32, 32)
        self.run_test(m, (256, 256), show_focus=True, allow_oob=True)

if __name__ == '__main__':
    unittest.main()
