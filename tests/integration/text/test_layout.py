"""Test creation of all Layout classes"""

import random
import itertools
import unittest

import pyglet
import pytest
from pyglet.text.effects import DropShadow

from pyglet.text import caret, document, decode_text, decode_attributed
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
@pytest.mark.parametrize('text', ['中文自动换行测试', '日本語の文章テスト', '한국어자동줄바꿈테스트'])
@pytest.mark.parametrize('wrap', [True, 'char'])
def test_cjk_wrapping(test_window, doctype, layouttype, text, wrap):
    doc = doctype(text)
    doc.set_style(0, len(text), {'wrap': wrap})
    glyphs, offsets = doc.get_font(0).get_glyphs(text)
    width = max(g.advance + offset.x_advance for g, offset in zip(glyphs, offsets)) * 2.5
    text_layout = layouttype(doc, width=width, height=200, multiline=True)
    try:
        lines = text_layout.lines if isinstance(text_layout, layout.IncrementalTextLayout) else text_layout._get_lines()
        assert len(lines) > 1
        assert sum(line.length for line in lines) == len(text)
        assert lines[0].start == 0
        assert all(a.start + a.length == b.start for a, b in zip(lines, lines[1:]))
        assert text_layout.content_width <= width
    finally:
        text_layout.delete()


@pytest.mark.parametrize('doctype', document_classes)
@pytest.mark.parametrize('wrap', [True, 'char'])
def test_incremental_cjk_reflow_matches_fresh_layout(test_window, doctype, wrap):
    doc = doctype('中文自动换行测试')
    doc.set_style(0, len(doc.text), {'wrap': wrap})
    glyphs, offsets = doc.get_font(0).get_glyphs(doc.text)
    width = max(g.advance + offset.x_advance for g, offset in zip(glyphs, offsets)) * 2.5
    incremental = layout.IncrementalTextLayout(doc, width=width, height=200, multiline=True)

    def assert_matches_fresh():
        fresh = layout.TextLayout(doc, width=incremental.width, height=200, multiline=True)
        try:
            old_lines = incremental.lines
            new_lines = fresh._get_lines()
            assert [(line.start, line.length) for line in old_lines] == [
                (line.start, line.length) for line in new_lines
            ]
            assert [line.width for line in old_lines] == pytest.approx([line.width for line in new_lines])
            assert incremental.content_width == fresh.content_width
        finally:
            fresh.delete()

    try:
        assert_matches_fresh()
        doc.insert_text(1, '（')
        doc.insert_text(4, '）')
        assert_matches_fresh()
        doc.insert_text(3, '\u0301')
        assert_matches_fresh()
        doc.insert_text(6, 'Python')
        assert_matches_fresh()
        doc.delete_text(1, 6)
        assert_matches_fresh()
        incremental.width = width * 1.5
        assert_matches_fresh()
        doc.text = '한국어자동줄바꿈テスト中文'
        assert_matches_fresh()
    finally:
        incremental.delete()


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


def test_text_layout_reuses_groups_until_group_state_changes(test_window):
    # Test to make sure labels don't disappear on group/state change.
    text_layout = layout.TextLayout(document.UnformattedDocument("Reusable groups"))
    try:
        original_groups = dict(text_layout.group_cache)
        text_layout._update()  # noqa: SLF001
        assert text_layout.group_cache == original_groups

        parent_group = pyglet.graphics.Group()
        text_layout.group = parent_group
        assert text_layout.group_cache
        assert all(group.parent is parent_group for group in text_layout.group_cache.values())
        assert not set(original_groups.values()).intersection(text_layout.group_cache.values())
    finally:
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


def test_caret_selection_scrolls_incremental_layout(test_window):
    text_layout = layout.IncrementalTextLayout(
        document.UnformattedDocument('A long line that must scroll'),
        width=50,
        height=100,
        multiline=False,
        depth_sorting=True,
    )
    text_caret = caret.Caret(text_layout)

    text_caret.mark = 0
    text_caret.position = len(text_layout.document.text)

    assert text_layout.view_x > 0
    assert text_caret._list.translation[3] == pytest.approx(text_layout.get_depth_offset(2))  # noqa: SLF001


@pytest.mark.parametrize('layouttype', layout_classes)
def test_layout_visibility_updates_glyphs_and_decorations(test_window, layouttype):
    doc = document.FormattedDocument('First line\nSecond line\nThird line')
    doc.set_style(0, len(doc.text), {'background_color': (50, 50, 50, 255),
                                    'underline': (255, 255, 255, 255), 'shadow': DropShadow()})
    text_layout = layouttype(doc, width=500, height=100, multiline=True)
    try:
        lines = text_layout.lines if isinstance(text_layout, layout.IncrementalTextLayout) else text_layout._lines
        vertex_lists = [vertex_list for line in lines
                        for box in line.boxes for vertex_list in box.vertex_lists]
        assert vertex_lists
        for visible in (False, True, False):
            text_layout.visible = visible
            assert text_layout.visible is visible
            assert vertex_lists == [vertex_list for line in lines
                                    for box in line.boxes for vertex_list in box.vertex_lists]
            assert all(all(value == visible for value in vertex_list.visible) for vertex_list in vertex_lists)
    finally:
        text_layout.delete()


def test_incremental_layout_remains_hidden_after_edits_and_scrolling(test_window):
    doc = document.FormattedDocument('\n'.join(['Some text'] * 20))
    text_layout = layout.IncrementalTextLayout(doc, width=200, height=50, multiline=True)
    try:
        text_layout.visible = False
        doc.insert_text(0, 'New text\n')
        text_layout.view_y = -text_layout.content_height
        for visible in (False, True):
            text_layout.visible = visible
            vertex_lists = [vertex_list for line in text_layout.lines for vertex_list in line.vertex_lists]
            assert vertex_lists
            assert all(all(value == visible for value in vertex_list.visible) for vertex_list in vertex_lists)
    finally:
        text_layout.delete()


@pytest.mark.parametrize('property_name', ['batch', 'group', 'depth_sorting'])
@pytest.mark.parametrize('deferred', [False, True])
def test_incremental_layout_render_properties_rebuild_all_lines(test_window, property_name, deferred):
    doc = document.FormattedDocument('First line\nSecond line\nThird line')
    doc.set_style(0, len(doc.text), {'background_color': (50, 50, 50, 255), 'shadow': DropShadow()})
    text_layout = layout.IncrementalTextLayout(doc, width=500, height=100, multiline=True)
    try:
        if property_name == 'batch':
            value = pyglet.graphics.Batch()
        elif property_name == 'group':
            value = pyglet.graphics.Group()
        else:
            value = True

        old_lists = [list(line.vertex_lists) for line in text_layout.lines]
        assert len(old_lists) == 3 and all(old_lists)
        if deferred:
            text_layout.begin_update()
        setattr(text_layout, property_name, value)
        if deferred:
            assert [line.vertex_lists for line in text_layout.lines] == old_lists
            text_layout.end_update()
        for line, previous in zip(text_layout.lines, old_lists):
            assert line.vertex_lists
            assert all(vertex_list not in previous for vertex_list in line.vertex_lists)
        if property_name == 'group':
            assert all(group.parent is value for group in text_layout.group_cache.values())
        elif property_name == 'batch':
            assert all(vertex_list.domain.batch is value
                       for line in text_layout.lines for vertex_list in line.vertex_lists)
        elif property_name == 'depth_sorting':
            assert any(vertex_list.translation[3] != 0
                       for line in text_layout.lines for vertex_list in line.vertex_lists)
        text_layout.draw()
    finally:
        text_layout.delete()


@pytest.mark.parametrize('property_name, value', [('content_halign', 'right'), ('content_valign', 'bottom'),
                                                ('height', 200)])
def test_incremental_layout_alignment_updates_all_lines(test_window, property_name, value):
    text_layout = layout.IncrementalTextLayout(
        document.UnformattedDocument('First line\nSecond line\nThird line'),
        width=500, height=100, multiline=True,
    )
    try:
        old_anchor = tuple(text_layout.lines[-1].vertex_lists[0].anchor[:2])
        setattr(text_layout, property_name, value)
        expected = {
            'content_halign': (500 - text_layout.content_width, 100),
            'content_valign': (0, text_layout.content_height),
            'height': (0, 200),
        }[property_name]
        assert expected != old_anchor
        for line in text_layout.lines:
            assert tuple(line.vertex_lists[0].anchor[:2]) == expected
        assert all(group.uniforms['scissor_area'] == (text_layout.left, text_layout.bottom, 500, text_layout.height)
                   for group in text_layout.group_cache.values())
    finally:
        text_layout.delete()


def test_incremental_layout_dpi_reflows_glyphs(test_window):
    text_layout = layout.IncrementalTextLayout(
        document.UnformattedDocument('Some text\nSome text'), width=500, height=200, multiline=True, dpi=96,
    )
    try:
        old_width = text_layout.content_width
        old_height = text_layout.content_height
        text_layout.dpi = 192
        assert text_layout.content_width > old_width
        assert text_layout.content_height > old_height
    finally:
        text_layout.delete()


def test_incremental_layout_draw_with_shared_batch(test_window, monkeypatch):
    batch = pyglet.graphics.Batch()
    text_layout = layout.IncrementalTextLayout(
        document.UnformattedDocument('First line\nSecond line'), width=500, height=100, multiline=True, batch=batch,
    )
    captured = []
    monkeypatch.setattr(batch, 'draw_subset', lambda vertex_lists: captured.extend(vertex_lists))
    try:
        text_layout.draw()
        expected = [vertex_list for line in text_layout.lines for vertex_list in line.vertex_lists]
        assert expected
        assert captured == expected
    finally:
        text_layout.delete()


def test_incremental_layout_visibility_updates_inline_elements(test_window):
    from pyglet.text.formats.structured import HorizontalRuleElement

    element = HorizontalRuleElement(color=(255, 255, 255, 255), width=10)
    doc = document.FormattedDocument('Text with element ')
    doc.insert_element(len(doc.text), element)
    text_layout = layout.IncrementalTextLayout(doc, width=200, height=100)
    try:
        for visible in (False, True):
            text_layout.visible = visible
            assert all(value == visible for value in element.vertex_lists[text_layout].visible)
    finally:
        text_layout.delete()


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


@pytest.mark.parametrize('text', ['a\t\tb', '\t\t', 'a\tb\n\t\t\tc'])
@pytest.mark.parametrize('shaping', [True, False])
def test_multiline_layout_with_consecutive_tabs(test_window, text, shaping):
    # Every character needs a glyph: a run of tabs has no glyph in some shapers (DirectWrite)
    font = pyglet.font.load(None, 12)
    glyphs, offsets = font.get_glyphs(text, shaping)
    assert len(glyphs) == len(offsets) == len(text)

    text_layout = layout.TextLayout(decode_text(text), width=WIDTH, multiline=True, shaping=shaping)
    text_layout.draw()
