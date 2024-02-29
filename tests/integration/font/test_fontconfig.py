"""
Tests for font integration in all platforms.
"""
from tests.annotations import Platform, skip_platform

from pyglet import font


@skip_platform(Platform.LINUX)  # Arial may not be installed
def test_have_font():
    """
    Test functionality to check for availability of fonts.
    """
    assert font.have_font('Arial')
    assert not font.have_font('missing-font-name')
