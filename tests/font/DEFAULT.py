#!/usr/bin/env python

'''Test that a font with no name given still renders using some sort
of default system font.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from . import base_text

class TEST_DEFAULT(base_text.TextTestBase):
    font_name = ''

if __name__ == '__main__':
    unittest.main()
