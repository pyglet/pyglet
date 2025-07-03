"""Tests for loading and accessing FreeType font faces."""
import pytest
from pyglet.enums import Weight, Style, Stretch

from tests.annotations import Platform, require_platform

try:
    from pyglet.font.freetype import FreeTypeFace, FreeTypeMemoryFace
    from pyglet.font.fontconfig import get_fontconfig
except ImportError:
    FreeTypeFace = None
    FreeTypeMemoryFace = None
    get_fontconfig = None


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,font_name,weight,style', [
    ('action_man.ttf', 'Action Man', Weight.NORMAL, Style.NORMAL),
    ('action_man_bold.ttf', 'Action Man', Weight.BOLD, Style.NORMAL),
    ('action_man_bold_italic.ttf', 'Action Man', Weight.BOLD, Style.ITALIC),
    ('action_man_italic.ttf', 'Action Man', Weight.NORMAL, Style.ITALIC),
])
def test_face_from_file(test_data, font_file_name, font_name, weight, style):
    """Test loading a font face directly from file."""
    face = FreeTypeFace.from_file(test_data.get_file('fonts', font_file_name))

    assert face.name == font_name
    assert face.family_name == font_name
    assert face.weight == weight
    assert face.style == style

    del face


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_name,weight,style', [
    ('Arial', Weight.NORMAL, Style.NORMAL),
    ('Arial', Weight.BOLD, Style.NORMAL),
    ('Arial', Weight.NORMAL, Style.ITALIC),
    ('Arial', Weight.BOLD, Style.ITALIC),
])
def test_face_from_fontconfig(font_name, weight, style):
    """Test loading a font face from the system using font config."""
    match = get_fontconfig().find_font(font_name, 16, weight, style)
    assert match is not None

    face = FreeTypeFace.from_fontconfig(match)

    assert face.weight == weight
    assert face.style == style

    del face


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,font_name,weight,style', [
    ('action_man.ttf', 'Action Man', Weight.NORMAL, Style.NORMAL),
    ('action_man_bold.ttf', 'Action Man', Weight.BOLD, Style.NORMAL),
    ('action_man_bold_italic.ttf', 'Action Man', Weight.BOLD, Style.ITALIC),
    ('action_man_italic.ttf', 'Action Man', Weight.NORMAL, Style.ITALIC),
])
def test_memory_face(test_data, font_file_name, font_name, weight, style):
    """Test loading a font into memory using FreeTypeMemoryFont."""
    with open(test_data.get_file('fonts', font_file_name), 'rb') as font_file:
        font_data = font_file.read()
    font = FreeTypeMemoryFace(font_data, 0)

    assert font.name == font_name
    assert font.weight == weight
    assert font.style == style
    assert font.ft_face is not None

    del font


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,size,dpi,ascent,descent', [
    ('action_man.ttf', 16, 96, 15, -4),
    ('action_man.ttf', 10, 96, 9, -3),
    ('action_man.ttf', 16, 72, 11, -3),
    ('courR12-ISO8859-1.pcf', 16, 96, 12, -3),

    # A fixed bitmap size font. Will fail if render size is used. Keep for legacy info.
    # ('courR12-ISO8859-1.pcf', 16, 96, 15, -4),
])
def test_face_metrics(test_data, font_file_name, size, dpi, ascent, descent):
    """Test a face from file and check the metrics."""
    face = FreeTypeFace.from_file(test_data.get_file('fonts', font_file_name))
    metrics = face.get_font_metrics(size, dpi)

    assert metrics.ascent == ascent
    assert metrics.descent == descent


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,character,index', [
    ('action_man.ttf', 'a', 65),
    ('action_man.ttf', 'A', 33),
    ('action_man.ttf', '1', 17),
    ('action_man.ttf', '#', 3),
    ('action_man.ttf', 'b', 66),
])
def test_character_index(test_data, font_file_name, character, index):
    """Test getting the glyph index for a character."""
    face = FreeTypeFace.from_file(test_data.get_file('fonts', font_file_name))
    assert face.get_character_index(character) == index


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,glyph_index', [
    ('action_man.ttf', 65),
    ('action_man.ttf', 33),
    ('action_man.ttf', 17),
    ('action_man.ttf', 3),
    ('action_man.ttf', 66),
])
def test_get_glyph_slot(test_data, font_file_name, glyph_index):
    """Test getting a glyph slot from the face."""
    face = FreeTypeFace.from_file(test_data.get_file('fonts', font_file_name))
    face.set_char_size(size=16, dpi=92)
    glyph = face.get_glyph_slot(glyph_index)

    assert glyph is not None
