"""
Tests for font integration in all platforms.
"""

from pyglet import font

def test_have_font():
    """
    Test functionality to check for availability of fonts.
    """
    assert font.have_font('Arial')
    assert not font.have_font('missing-font-name')

