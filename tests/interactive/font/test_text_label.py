"""
Tests for the basic font.Text label.
"""
import pytest

from .font_test_base import font_fixture


@pytest.mark.parametrize('halign', [
    'left',
    'center',
    'right',
    ])
def test_text_halign(font_fixture, halign):
    """Test that font.Text horizontal alignment works.

    Three labels will be rendered aligned left, center and right.
    """
    font_fixture.test_font(
            question='Is the text horizontally {} aligned?'.format(halign),
            text=halign.upper(),
            text_options={'halign': halign},
            fill_width=True
            )

@pytest.mark.parametrize('valign,desc', [
    ('top', 'The line should be above the capitals.'),
    ('center', 'The line should be in the middle of the capitals.'),
    ('baseline', 'The line should be at the bottom of the capitals.'),
    ('bottom', 'The line should be at the bottom of the lower case y.')
    ])
def test_text_valign(font_fixture, valign, desc):
    """Test that font.Text vertical alignment works."""
    font_fixture.test_font(
            question='Is the text vertically {} aligned?\n{}'.format(valign, desc),
            text=valign.upper() + ' y',
            text_options={'valign': valign},
            draw_baseline=True
            )
