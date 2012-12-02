#!/usr/bin/env python

'''Test that rendering of bullet glyphs works.

You should see 5 bullet glyphs rendered in the bottom-left of the window.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import font

from . import base_text

class TEST_HALIGN(base_text.TextTestBase):
    font_name = ''
    font_size = 60
    text = u'\u2022'*5

if __name__ == '__main__':
    unittest.main()
