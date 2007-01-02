#!/usr/bin/env python

'''Testing rect map debug rendering.

Press "s" to switch between lines and checkered display.

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase, DummyImage, gencells
import pyglet.scene2d

class RectFlatDebugTest(RenderBase):
    def test_main(self):
        m = pyglet.scene2d.Map(32, 32, gencells(['a'*10]*10, 32, 32,
            pyglet.scene2d.Cell))
        self.run_test(m)

if __name__ == '__main__':
    unittest.main()
