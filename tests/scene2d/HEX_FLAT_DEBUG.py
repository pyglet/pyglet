#!/usr/bin/env python

'''Testing hex map debug rendering.

You should see a checkered hex map.

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase
import pyglet.scene2d
from pyglet.scene2d.debug import gen_hex_map

class HexFlatDebugTest(RenderBase):
    def test_main(self):
        m = gen_hex_map(['a'*10]*10, 32)
        self.set_map(m)
        self.view.allow_oob = False
        self.run_test()

if __name__ == '__main__':
    unittest.main()
