#!/usr/bin/env python

'''Testing loading of a map.

You should see a simple map with a circular road on it.
The tiles are not well-designed :)

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import unittest
from render_base import RenderBase
import pyglet.scene2d

class MapLoadTest(RenderBase):
    def test_main(self):
        map_xml = os.path.join(os.path.dirname(__file__), 'map.xml')

        self.init_window(256, 256)
        m = pyglet.scene2d.RectMap.load_xml(map_xml)
        self.run_test(m, show_focus=True, debug=False)

if __name__ == '__main__':
    unittest.main()
