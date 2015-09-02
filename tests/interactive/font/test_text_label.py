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
    w = font_fixture.create_window()
    w.draw_metrics=True,
    w.create_label(
            text=halign.upper(),
            halign=halign,
            fill_width=True,
            margin=0,
            )
    font_fixture.ask_question(
            'Is the text horizontally {} aligned?'.format(halign),
            )

@pytest.mark.parametrize('valign,desc', [
    ('top', 'The line should be above the capitals.'),
    ('center', 'The line should be in the middle of the capitals.'),
    ('baseline', 'The line should be at the bottom of the capitals.'),
    ('bottom', 'The line should be at the bottom of the lower case y.')
    ])
def test_text_valign(font_fixture, valign, desc):
    """Test that font.Text vertical alignment works."""
    w = font_fixture.create_window()
    w.draw_baseline = True
    w.create_label(
            text=valign.upper() + ' y',
            valign=valign,
            )
    font_fixture.ask_question(
            'Is the text vertically {} aligned?\n{}'.format(valign, desc),
            )


@pytest.mark.parametrize('valign,halign', [
    ('top', 'left'),
    ('center', 'center'),
    ('bottom', 'right')
    ])
def test_multiline_alignment(font_fixture, valign, halign):
    """Test horizontal and vertical alignment with multi line text."""
    w = font_fixture.create_window(
            height=500,
            )
    w.create_label(
            text='This text with multiple lines is aligned {}-{}'.format(valign, halign),
            halign=halign,
            valign=valign,
            fill_width=True,
            margin=0,
            )
    w.draw_baseline = True
    font_fixture.ask_question(
            'Is the text aligned {}-{}?'.format(valign, halign)
            )


@pytest.mark.parametrize('text,question', [
    ('TEST TEST', 'TEST TEST should bo on a single line.'),
    ('SPAM SPAM\nSPAM', 'SPAM should we twice on the first line, once on the second.')
    ])
def test_wrap_invariant(font_fixture, text, question):
    """Test that text will not wrap when its width is set to its calculated width."""
    w = font_fixture.create_window()
    l = w.create_label(
            text=text
            )
    l.width = l.width + 1
    font_fixture.ask_question(
            question
            )
