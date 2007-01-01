#!/usr/bin/env python

'''Testing flat map scrolling.

Press arrow keys to move view focal point (red dot) around map.

You will be able to move "off" the map.

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase, DummyImage
import pyglet.scene2d

class HexFlatDebugTest(RenderBase):
    def test_main(self):
        m = pyglet.scene2d.HexMap(32, images=[[DummyImage()]*10]*10)
        self.run_test(m, (256, 256), show_focus=True)

if __name__ == '__main__':
    unittest.main()
