from .font_test_base import FontTestBase

import pyglet
from tests.annotations import Platform


class FontTestCase(FontTestBase):
    window_size = 400, 100


color_description = "Test that font colour is applied correctly."

FontTestCase.create_test_case(
        name='test_opacity_0dot1',
        description=color_description,
        question='Default font should appear at 0.1 opacity (faint white)',
        color=(1, 1, 1, 0.1)
        )

FontTestCase.create_test_case(
        name='test_opacity_0',
        description=color_description,
        question='Text should not be visible due to opacity=0',
        color=(1, 1, 1, 0)
        )

FontTestCase.create_test_case(
        name='test_opacity_1',
        description=color_description,
        question='Default font should appear at full opacity (white)',
        color=(1, 1, 1, 1)
        )

FontTestCase.create_test_case(
        name='test_color_blue',
        description=color_description,
        question='Default font should appear blue',
        color=(0, 0, 1, 1)
        )

FontTestCase.create_test_case(
        name='test_color_red',
        description=color_description,
        question='Default font should appear red',
        color=(1, 0, 0, 1)
        )


default_font_description = """Test that a font with no name given still renders using some sort
    of default system font.
    """

FontTestCase.create_test_case(
        name='test_default_font',
        description=default_font_description,
        question='Font should be rendered using a default system font',
        font_name=''
        )


system_font_description = """Test that a font likely to be installed on the computer can be
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

FontTestCase.create_test_case(
        name='test_system_font_' + font_name,
        description=system_font_description,
        font_name=font_name,
        question='"Quickly brown fox" should be shown at 24pt using font ' + font_name
        )


unicode_description = """Test that rendering of unicode glyphs works."""

FontTestCase.create_test_case(
        name='test_bullet_glyphs',
        description=unicode_description,
        font_size = 60,
        text = u'\u2022'*5,
        question = 'You should see 5 bullet glyphs rendered in the bottom-left of the window.'
        )


large_font_description = "Render a font using a very large size. Tests issue 684."

FontTestCase.create_test_case(
        name='test_large_font',
        description=large_font_description,
        font_name='Arial',
        font_size=292,
        text='trawant',
        window_size=(1000, 400),
        question='Is the word "trawant" rendered in a large font?'
        )

