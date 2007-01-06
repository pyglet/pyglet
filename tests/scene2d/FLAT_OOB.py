#!/usr/bin/env python

'''Testing flat map allow_oob enforcement.

Press arrow keys to move view focal point (red dot) around map.
Press "o" to turn allow_oob on and off.

You should see no black border with allow_oob=False.

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
        m = pyglet.scene2d.Map(32, 32, genmap(['a'*10]*10, 32, 32,
            pyglet.scene2d.Cell))
        self.run_test(m, (256, 256), show_focus=True)

if __name__ == '__main__':
    unittest.main()
