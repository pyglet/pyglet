#!/usr/bin/env python

'''Test that font.Text horizontal alignment works.

Three labels will be rendered aligned left, center and right.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import font

import base_text

class TEST_HALIGN(base_text.TextTestBase):
    font_name = ''
    font_size = 60
    text = u'\u2022'*5

if __name__ == '__main__':
    unittest.main()
