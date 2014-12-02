#!/usr/bin/env python

"""
Render a font using a large size. Tests issue 684.
"""
__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from . import base_text


class TEST_LARGE_FONT(base_text.TextTestBase):
    font_name = 'Arial'
    font_size = 292
    text = 'trawant'
    window_size = 800, 400

if __name__ == '__main__':
    unittest.main()
