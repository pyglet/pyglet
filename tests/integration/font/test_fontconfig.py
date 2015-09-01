"""
Tests for font integration in all platforms.
"""

import unittest
from pyglet import font

class FontPlatformIntegrationTestCase(unittest.TestCase):
    def test_have_font(self):
        """
        Test functionality to check for availability of fonts.
        """
        self.assertTrue(font.have_font('Arial'))
        self.assertFalse(font.have_font('missing-font-name'))

