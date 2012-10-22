#!/usr/bin/env python

'''Test that text will not wrap when its width is set to its calculated
width.

You should be able to clearly see "TEST TEST" on a single line (not two)
and "SPAM SPAM SPAM" over two lines, not three.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
from . import base_text
from pyglet import font

class TEST_WRAP_INVARIANT(base_text.TextTestBase):
    font_name = ''
    text = 'TEST TEST'

    def render(self):
        fnt = font.load('', 24)
        self.label1 = font.Text(fnt, 'TEST TEST', 10, 150)
        self.label1.width = self.label1.width + 1
        self.label2 = font.Text(fnt, 'SPAM SPAM\nSPAM', 10, 50)
        self.label2.width = self.label2.width + 1

    def draw(self):
        self.label1.draw()
        self.label2.draw()

if __name__ == '__main__':
    unittest.main()
