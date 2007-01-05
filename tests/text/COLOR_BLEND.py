#!/usr/bin/env python

'''Test that font colour is applied correctly.   Default font should
appear at 0.1 opacity (faint white)
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_text
from pyglet.scene2d.textsprite import *

class TEST_COLOR_BLEND(base_text.TextTestBase):
    font_name = ''
    font_size = 72

    def render(self):
        self.sprite = TextSprite(self.font, self.text, color=(1, 1, 1, 0.1))

if __name__ == '__main__':
    unittest.main()
