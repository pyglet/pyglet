#!/usr/bin/env python

'''Test that a font likely to be installed on the computer can be
loaded and displayed correctly.

One window will open, it should show "Quickly brown fox" at 24pt using:


'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import sys
import base_text

from pyglet import font

class TEST_CUSTOM(base_text.TextTestBase):
    font_name = 'Aapex'
    font_size = 24

    def create_font(self):
        font.add_file('/home/a/aholkner/Aapex.ttf')
        super(TEST_CUSTOM, self).create_font()

if __name__ == '__main__':
    unittest.main()
