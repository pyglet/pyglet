"""
Test font loading and rendering.
"""
import pytest

import pyglet
from pyglet import font
from tests.annotations import Platform
from .font_test_base import font_fixture


@pytest.mark.parametrize('question,color', [
    ('Default font should appear at 0.3 opacity (faint grey)', (0, 0, 0, 0.3)),
    ('Text should not be visible due to opacity 0.0', (0, 0, 0, 0)),
    ('Default font should appear at full opacity (black)', (0, 0, 0, 1)),
    ('Default font should appear blue', (0, 0, 1, 1)),
    ('Default font should appear red', (1, 0, 0, 1)),
    ])
def test_color(font_fixture, question, color):
    """Test that font colour is applied correctly."""
    w = font_fixture.create_window()
    w.create_label(
            color=color
            )
    font_fixture.ask_question(question)


def test_default_font(font_fixture):
    """Test that a font with no name given still renders using some sort
    of default system font.
    """
    w = font_fixture.create_window()
    w.load_font(
            name=''
            )
    w.create_label()
    font_fixture.ask_question(
            'Font should be rendered using a default system font'
            )


def test_system_font(font_fixture):
    """Test that a font likely to be installed on the computer can be
    loaded and displayed correctly.

    One window will open, it should show "Quickly brown fox" at 24pt using:

    * "Helvetica" on Mac OS X
    * "Arial" on Windows
    * "Arial" on Linux
    """

    if pyglet.compat_platform in Platform.OSX:
        font_name = 'Helvetica'
    elif pyglet.compat_platform in Platform.WINDOWS:
        font_name = 'Arial'
    else:
        font_name = 'Arial'

    w = font_fixture.create_window()
    w.load_font(
            name=font_name
            )
    w.create_label()
    font_fixture.ask_question(
            '"Quickly brown fox" should be shown at 24pt using font ' + font_name
            )


def test_bullet_glyphs(font_fixture):
    """Test that rendering of unicode glyphs works."""

    w = font_fixture.create_window()
    w.load_font(
            size=60
            )
    w.create_label(
            text=u'\u2022'*5,
            )
    font_fixture.ask_question(
        'You should see 5 bullet glyphs.'
        )


def test_large_font(font_fixture):
    "Render a font using a very large size. Tests issue 684."

    w = font_fixture.create_window(
            width=1000,
            height=400,
            )
    w.load_font(
            name='Arial',
            size=292,
            )
    w.create_label(
            text='trawant',
            )
    font_fixture.ask_question(
            'Is the word "trawant" rendered in a large font?'
            )


@pytest.mark.parametrize('font_desc,font_file, font_options', [
    ('regular', 'action_man.ttf', {}),
    ('bold', 'action_man_bold.ttf', {'bold':True}),
    ('italic', 'action_man_italic.ttf', {'italic':True}),
    ('bold italic', 'action_man_bold_italic.ttf', {'bold':True, 'italic':True})
    ])
def test_add_font(font_fixture, test_data, font_desc, font_file, font_options):
    """Test that a font distributed with the application can be displayed.

    Four lines of text should be displayed, each in a different variant
    (bold/italic/regular) of Action Man at 24pt.  The Action Man fonts are
    included in the test data directory (tests/data/fonts) as action_man*.ttf.
    """
    font.add_file(test_data.get_file('fonts', font_file))
    w = font_fixture.create_window()
    w.load_font(
            name='Action Man',
            **font_options
            )
    w.create_label()
    font_fixture.ask_question(
            """You should see {} style Action Man at 24pt.""".format(font_desc)
            )

@pytest.mark.parametrize('font_name,text', [
        ('Action man', 'Action Man'),
        ('Action man', 'Action Man longer test with more words'),
        ('Arial', 'Arial'),
        ('Arial', 'Arial longer test with more words'),
        ('Times New Roman', 'Times New Roman'),
        ('Times New Roman', 'Times New Roman longer test with more words'),
    ])
def test_horizontal_metrics(font_fixture, test_data, font_name, text):
    """Test that the horizontal font metrics are calculated correctly.

    Some text in various fonts will be displayed.  Green vertical lines mark
    the left edge of the text.  Blue vertical lines mark the right edge of the
    text.
    """
    font.add_file(test_data.get_file('fonts', 'action_man.ttf'))
    question=("The green vertical lines should match the left edge of the text"
            + "and the blue vertical lines should match the right edge of the text.")
    w = font_fixture.create_window(
            width=600,
            )
    w.draw_metrics = True
    w.load_font(
            name=font_name,
            size=16,
            )
    w.create_label(
            text=text,
            )
    font_fixture.ask_question(
            question,
            )

def test_metrics_workaround(font_fixture, test_data):
    """Test workaround for font missing metrics.

    Font should fit between top and bottom lines.
    """
    font.add_file(test_data.get_file('fonts', 'courR12-ISO8859-1.pcf'))
    w = font_fixture.create_window(
            width=600,
            )
    w.draw_metrics = True
    w.load_font(
            name='Courier',
            size=16,
            )
    w.create_label(
            text='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            )
    font_fixture.ask_question(
            'The text should fit between the top and bottom lines',
            )

#@pytest.mark.parametrize('dpi,width,height', [
#    (120, 9, 27),
#    ])
#def test_dpi(font_fixture, test_data, dpi, width, height):
#    font.add_file(test_data.get_file('fonts', 'action_man.ttf'))
#    question=("The green vertical lines should match the left edge of the text"
#            + "and the blue vertical lines should match the right edge of the text.")
#    font_fixture.test_font(
#            font_name='Action Man',
#            font_size=16,
#            font_options={'dpi': dpi},
#            question=question,
#            draw_metrics=True,
#            text='The DPI is {}'.format(dpi),
#            text_options = {
#                'width': width,
#                'height': height,
#                }
#            )
