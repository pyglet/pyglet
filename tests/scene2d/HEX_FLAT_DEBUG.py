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
        self.run_test(gen_hex_map(['a'*10]*10, 32))

if __name__ == '__main__':
    unittest.main()
