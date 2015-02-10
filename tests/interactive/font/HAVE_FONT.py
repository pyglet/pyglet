#!/usr/bin/env python

'''Test that font.have_font() function works correctly.'''

import unittest
from pyglet import font

__noninteractive = True

class HAVE_FONT(unittest.TestCase):
    def test_have_font(self):
        self.assertTrue(font.have_font('Arial'))
        self.assertFalse(font.have_font('missing-font-name'))

if __name__ == '__main__':
    unittest.main()
