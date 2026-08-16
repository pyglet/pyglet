"""Test creation of all Layout classes"""

import random
import itertools
import unittest

import pyglet
import pytest

from pyglet.text import document, decode_text, decode_attributed
from pyglet.text import layout

WIDTH = 500
HEIGHT = 100
X = random.randint(0, 900)
Y = random.randint(0, 600)
Z = random.randint(-10, 10)


# Create combination of all Layout and Document types
document_classes = [document.UnformattedDocument, document.FormattedDocument]
layout_classes = [layout.TextLayout, layout.ScrollableTextLayout, layout.IncrementalTextLayout]
all_combinations = list(itertools.product(document_classes, layout_classes))


@pytest.mark.parametrize('doctype, layouttype', all_combinations)
def test_layout_creation_keyword(test_window, doctype, layouttype):
    _doc = doctype("This is a test")
    _layout = layouttype(document=_doc, x=X, y=Y, z=Z, width=WIDTH, height=HEIGHT)
    assert _layout.x == X
    assert _layout.y == Y
    assert _layout.z == Z
    assert _layout.width == WIDTH
    assert _layout.height == HEIGHT
    assert _layout.position == (X, Y, Z)


@pytest.mark.parametrize('doctype, layouttype', all_combinations)
def test_layout_creation_positional(test_window, doctype, layouttype):
    _doc = doctype("This is a test")
    _layout = layouttype(_doc, X, Y, Z, WIDTH, HEIGHT)
    # Make sure the arguments were in order:
    assert _layout.x == X
    assert _layout.y == Y
    assert _layout.z == Z
    assert _layout.width == WIDTH
    assert _layout.height == HEIGHT
    assert _layout.position == (X, Y, Z)


def test_layout_get_as_texture(test_window):
    test_window.switch_to()
    text_layout = layout.TextLayout(document.UnformattedDocument("Render texture"), x=100, y=50)
    original_position = text_layout.position
    texture = text_layout.get_as_texture()

    try:
        assert texture.width == round(text_layout.content_width)
        assert texture.height == round(text_layout.content_height)
        assert text_layout.position == original_position

        pixels = bytes(texture.fetch().get_bytes("RGBA", texture.width * 4))
        assert any(alpha > 0 for alpha in pixels[3::4])
    finally:
        texture.delete()
        text_layout.delete()


def test_layout_get_as_texture_with_reusable_target(test_window):
    test_window.switch_to()
    render_target = pyglet.graphics.TextureRenderTarget()
    layouts = [
        layout.TextLayout(document.UnformattedDocument("First")),
        layout.TextLayout(document.UnformattedDocument("A different sized label")),
    ]
    framebuffer = render_target.framebuffer
    camera = render_target.camera
    textures = []

    try:
        for text_layout in layouts:
            textures.append(text_layout.get_as_texture(render_target))
            assert render_target.framebuffer is framebuffer
            assert render_target.camera is camera
            assert render_target.texture is None

        assert textures[0].id != textures[1].id
        assert textures[0].width != textures[1].width
    finally:
        render_target.delete()
        for texture in textures:
            texture.delete()
        for text_layout in layouts:
            text_layout.delete()


def test_text_layout_reuses_groups_until_group_state_changes(test_window, monkeypatch):
    # Test to make sure labels don't disappear on group/state change.
    text_layout = layout.TextLayout(document.UnformattedDocument("Reusable groups"))
    original_groups = dict(text_layout.group_cache)

    text_layout._update()  # noqa: SLF001
    assert text_layout.group_cache == original_groups

    monkeypatch.setattr(text_layout, "_update", lambda: None)
    text_layout.program = object()  # type: ignore[assignment]
    assert not text_layout.group_cache

    text_layout.delete()


def test_incremental_layout_selection_creates_background_decoration(test_window):
    text_layout = layout.IncrementalTextLayout(
        document.FormattedDocument("aaaaaaaa"),
        width=500,
        height=100,
    )

    text_layout.set_selection(4, 8)
    decoration_lists = [vertex_list for line in text_layout.lines for vertex_list in line.vertex_lists]

    assert any(
        vertex_list.count == 4 and tuple(vertex_list.colors[:4]) == text_layout.selection_background_color
        for vertex_list in decoration_lists
    )


class TestIssues(unittest.TestCase):

    def test_issue471(self):
        doc = document.FormattedDocument()
        layout.IncrementalTextLayout(doc, 100, 100, width=500, height=100)
        doc.insert_text(0, "hello", {'bold': True})
        doc.text = ""

    def test_issue471_comment2(self):
        doc2 = decode_attributed('{bold True}a')
        incremental_layout = layout.IncrementalTextLayout(doc2, 100, 10, width=500, height=100)
        incremental_layout.document.delete_text(0, len(incremental_layout.document.text))

    def test_issue241_comment4a(self):
        doc = document.FormattedDocument("")
        layout.IncrementalTextLayout(doc, 50, 50, width=500, height=100)
        doc.set_style(0, len(doc.text), {"font_name": "Arial"})

    def test_issue241_comment4b(self):
        doc = document.FormattedDocument("test")
        layout.IncrementalTextLayout(doc, 50, 50, width=500, height=100)
        doc.set_style(0, len(doc.text), {"font_name": "Arial"})
        doc.delete_text(0, len(doc.text))

    def test_issue241_comment5(self):
        doc = document.FormattedDocument('A')
        doc.set_style(0, 1, dict(bold=True))
        layout.IncrementalTextLayout(doc, 100, 100, width=500, height=100)
        doc.delete_text(0, 1)

    def test_issue429_comment4a(self):
        doc = decode_attributed('{bold True}Hello{bold False}\n\n\n\n')
        doc2 = decode_attributed('{bold True}Goodbye{bold False}\n\n\n\n')
        incremental_layout = layout.IncrementalTextLayout(doc, 100, 10, width=500, height=100)
        incremental_layout.document = doc2
        incremental_layout.document.delete_text(0, len(incremental_layout.document.text))

    def test_issue429_comment4b(self):
        doc2 = decode_attributed('{bold True}a{bold False}b')
        incremental_layout = layout.IncrementalTextLayout(doc2, 100, 10, width=500, height=100)
        incremental_layout.document.delete_text(0, len(incremental_layout.document.text))


def test_incrementallayout_get_position_on_line_before_start_of_text(test_window):
    single_line_text = "This is a single line of text."
    doc = document.UnformattedDocument(single_line_text)
    font = doc.get_font()
    incremental_layout = layout.IncrementalTextLayout(
        doc, height=font.ascent - font.descent, width=200, multiline=False
    )
    incremental_layout.x = 100
    incremental_layout.y = 100

    assert incremental_layout.get_position_on_line(0, 100) == 0
    assert incremental_layout.get_position_on_line(0, 90) == 0
    assert incremental_layout.get_position_on_line(0, 80) == 0
    assert incremental_layout.get_position_on_line(0, 70) == 0
    assert incremental_layout.get_position_on_line(0, 60) == 0
    assert incremental_layout.get_position_on_line(0, 50) == 0


def test_incremental_layout_hit_testing_and_decorations_match_glyph_positions(test_window):
    doc = document.FormattedDocument("abcd")
    doc.set_style(1, 3, {"underline": (0, 0, 0, 255)})
    incremental_layout = layout.IncrementalTextLayout(doc, width=200, height=100, multiline=False)
    line = incremental_layout.lines[0]
    glyph_box = line.boxes[0]

    for position in range(glyph_box.length):
        left = line.x + glyph_box.get_point_in_box(position)
        right = line.x + glyph_box.get_point_in_box(position + 1)
        assert incremental_layout.get_position_on_line(0, left + (right - left) * 0.25) == position
        assert incremental_layout.get_position_on_line(0, left + (right - left) * 0.75) == position + 1

    underline_list = next(vertex_list for vertex_list in glyph_box.vertex_lists if vertex_list.count == 2)
    assert underline_list.position[0] == line.x + glyph_box.get_point_in_box(1)
    assert underline_list.position[3] == line.x + glyph_box.get_point_in_box(3)

    incremental_layout.set_selection(0, 3)
    background_list = next(vertex_list for vertex_list in glyph_box.vertex_lists if vertex_list.count == 8)
    assert list(background_list.indices) == [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7]
