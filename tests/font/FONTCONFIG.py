#!/usr/bin/env python

"""
Tests for fontconfig implementation.
"""
__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.font.fontconfig import get_fontconfig

__noninteractive = True


class TEST_DEFAULT(unittest.TestCase):
    def test_find_font_existing(self):
        font_match = get_fontconfig().find_font('arial')

        self.assertIsNotNone(font_match)
        self.assertIsNotNone(font_match.name)
        self.assertIsNotNone(font_match.file)

        # Face does not seem to work
        #self.assertIsNotNone(font_match.face)

    def test_find_font_match_name(self):
        font_match = get_fontconfig().find_font('arial')

        self.assertIsNotNone(font_match)
        self.assertEqual(font_match.name.lower(), 'arial')
        self.assertIn('arial', font_match.file.lower())

    def test_find_font_default(self):
        font_match = get_fontconfig().find_font(None)

        self.assertIsNotNone(font_match)
        self.assertIsNotNone(font_match.name)
        self.assertIsNotNone(font_match.file)

    def test_find_font_no_match(self):
        """Even if the font does not exist we get a default result."""
        font_match = get_fontconfig().find_font('unknown')

        self.assertIsNotNone(font_match)
        self.assertIsNotNone(font_match.name)
        self.assertIsNotNone(font_match.file)
        self.assertNotEqual(font_match.name.lower(), 'unknown')
        self.assertNotIn('unknown', font_match.file.lower())


if __name__ == '__main__':
    unittest.main()
