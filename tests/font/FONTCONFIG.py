#!/usr/bin/env python

"""
Tests for fontconfig implementation.
"""
__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.font.fontconfig import get_fontconfig

__noninteractive = True


class TEST_FONTCONFIG(unittest.TestCase):
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

    def test_find_font_match_size(self):
        font_match = get_fontconfig().find_font('arial', size=16.0)

        self.assertIsNotNone(font_match)
        self.assertEqual(font_match.name.lower(), 'arial')
        self.assertIn('arial', font_match.file.lower())
        self.assertEqual(font_match.size, 16.0)
        self.assertFalse(font_match.bold)
        self.assertFalse(font_match.italic)

    def test_find_font_match_bold(self):
        font_match = get_fontconfig().find_font('arial', size=12.0, bold=True)

        self.assertIsNotNone(font_match)
        self.assertEqual(font_match.name.lower(), 'arial')
        self.assertIn('arial', font_match.file.lower())
        self.assertEqual(font_match.size, 12.0)
        self.assertTrue(font_match.bold)
        self.assertFalse(font_match.italic)

    def test_find_font_match_italic(self):
        font_match = get_fontconfig().find_font('arial', size=12.0, italic=True)

        self.assertIsNotNone(font_match)
        self.assertEqual(font_match.name.lower(), 'arial')
        self.assertIn('arial', font_match.file.lower())
        self.assertEqual(font_match.size, 12.0)
        self.assertFalse(font_match.bold)
        self.assertTrue(font_match.italic)


if __name__ == '__main__':
    unittest.main()
