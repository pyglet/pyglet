import pytest

from pyglet import font
from .font_test_base import font_fixture


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
    font_fixture.test_font(
            font_name='Action Man',
            font_options=font_options,
            question="""You should see {} style Action Man at 24pt.""".format(font_desc)
             )

