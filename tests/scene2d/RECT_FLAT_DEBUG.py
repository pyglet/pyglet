#!/usr/bin/env python

'''Testing rect map debug rendering.

You should see a checkered square grid.

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase
import pyglet.scene2d
from pyglet.scene2d.debug import gen_rect_map

class RectFlatDebugTest(RenderBase):
    def test_main(self):
        m = pyglet.scene2d.RectMap(32, 32, gen_rect_map(['a'*10]*10, 32, 32))
        self.run_test(m)

if __name__ == '__main__':
    unittest.main()
