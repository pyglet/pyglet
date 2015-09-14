"""Tests for loading and accessing FreeType font faces."""
import pytest

from tests.annotations import Platform, require_platform

try:
    from pyglet.font.freetype import FreeTypeFace, FreeTypeMemoryFace
    from pyglet.font.fontconfig import get_fontconfig
except ImportError:
    FreeTypeFace = None
    FreeTypeMemoryFace = None
    get_fontconfig = None


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,font_name,bold,italic', [
    ('action_man.ttf', 'Action Man', False, False),
    ('action_man_bold.ttf', 'Action Man', True, False),
    ('action_man_bold_italic.ttf', 'Action Man', True, True),
    ('action_man_italic.ttf', 'Action Man', False, True),
    ])
def test_face_from_file(test_data, font_file_name, font_name, bold, italic):
    """Test loading a font face directly from file."""
    face = FreeTypeFace.from_file(test_data.get_file('fonts', font_file_name))

    assert face.name == font_name
    assert face.family_name == font_name
    assert face.bold == bold
    assert face.italic == italic

    del face


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_name,bold,italic', [
    ('Arial', False, False),
    ('Arial', True, False),
    ('Arial', False, True),
    ('Arial', True, True),
    ])
def test_face_from_fontconfig(font_name, bold, italic):
    """Test loading a font face from the system using font config."""
    match = get_fontconfig().find_font(font_name, 16, bold, italic)
    assert match is not None

    face = FreeTypeFace.from_fontconfig(match)

    assert face.name == font_name
    assert face.family_name == font_name
    assert face.bold == bold
    assert face.italic == italic

    del face


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,font_name,bold,italic', [
    ('action_man.ttf', 'Action Man', False, False),
    ('action_man_bold.ttf', 'Action Man', True, False),
    ('action_man_bold_italic.ttf', 'Action Man', True, True),
    ('action_man_italic.ttf', 'Action Man', False, True),
    ])
def test_memory_face(test_data, font_file_name, font_name, bold, italic):
    """Test loading a font into memory using FreeTypeMemoryFont."""
    with open(test_data.get_file('fonts', font_file_name), 'rb') as font_file:
        font_data = font_file.read()
    font = FreeTypeMemoryFace(font_data)

    assert font.name == font_name
    assert font.bold == bold
    assert font.italic == italic
    assert font.ft_face is not None

    del font


@require_platform(Platform.LINUX)
@pytest.mark.parametrize('font_file_name,size,dpi,ascent,descent', [
    ('action_man.ttf', 16, 96, 15, -4),
    ('action_man.ttf', 10, 96, 9, -3),
    ('action_man.ttf', 16, 72, 11, -3),
    ('courR12-ISO8859-1.pcf', 16, 96, 15, -4),
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

