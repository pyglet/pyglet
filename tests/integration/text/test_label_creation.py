"""Test creation of all Label classes and decoders"""
import random

import pytest


import pyglet
from pyglet.text import decode_text, decode_attributed, decode_html, DropShadow, LinearGradient, Stroke
from pyglet.text.document import FormattedDocument
from pyglet.text.layout import IncrementalTextLayout, get_default_layout_shader
from pyglet.text import DocumentLabel, HTMLLabel, Label

WIDTH = 500
HEIGHT = 100
X = random.randint(0, 900)
Y = random.randint(0, 600)
Z = random.randint(-10, 10)


@pytest.mark.parametrize('label_class', [Label, HTMLLabel])
@pytest.mark.parametrize('shaping', [True, False])
def test_label_creation(test_window, label_class, shaping):
    label = label_class("This is a test", x=X, y=Y, z=Z, shaping=shaping)
    assert label.x == X
    assert label.y == Y
    assert label.z == Z
    assert label._shaping is shaping  # noqa: SLF001


@pytest.fixture(params=[(decode_text, "This is a string of regular text."),
                        (decode_html, "<font color=green>This is html text.</font>"),
                        (decode_attributed, "This is {bold True}attributed{bold False} text.")])
def document(request):
    decoder, string = request.param
    return decoder(string)

@pytest.mark.parametrize('shaping', [True, False])
def test_documentlabel_creation(test_window, document, shaping):
    label = DocumentLabel(document=document, x=X, y=Y, z=Z, shaping=shaping)
    assert label.x == X
    assert label.y == Y
    assert label.z == Z
    assert label._shaping is shaping  # noqa: SLF001


def test_regular_labels_share_their_text_group(test_window):
    batch = pyglet.graphics.Batch()
    first = Label("First", batch=batch)
    second = Label("Second", batch=batch)

    first_group = first._boxes[0]._glyph_vertex_list.group  # noqa: SLF001
    second_group = second._boxes[0]._glyph_vertex_list.group  # noqa: SLF001

    assert first_group == second_group
    assert hash(first_group) == hash(second_group)
    assert batch.top_groups == [first_group]


def test_incremental_layout_can_create_decorations(test_window):
    document = FormattedDocument("Decorated")
    document.set_style(0, len(document.text), {"underline": (255, 0, 0, 255)})

    layout = IncrementalTextLayout(document, width=200, height=100)

    assert layout.has_view_translation


def test_regular_label_decoration_uses_non_scrollable_shader(test_window):
    label = Label("Decorated")
    label.document.set_style(0, len(label.document.text), {"underline": (255, 0, 0, 255)})

    assert not label.has_view_translation


def test_label_linear_gradient(test_window):
    gradient = LinearGradient((255, 0, 0, 255), (0, 0, 255, 255))
    label = Label("Gradient", color=gradient)

    colors = tuple(label._boxes[0]._glyph_vertex_list.colors)  # noqa: SLF001
    assert label.color is gradient
    assert colors[:8] == gradient.start * 2
    assert colors[-8:] == gradient.end * 2


@pytest.mark.parametrize(("style_name", "effect"), [
    ("shadow", lambda gradient: DropShadow(color=gradient)),
    ("stroke", lambda gradient: Stroke(color=gradient)),
])
def test_label_effect_linear_gradient(test_window, style_name, effect):
    gradient = LinearGradient((255, 0, 0, 255), (0, 0, 255, 255))
    label = Label("Gradient", **{style_name: effect(gradient)})

    vertex_lists = label._boxes[0].vertex_lists  # noqa: SLF001
    if style_name == "shadow":
        assert len(vertex_lists) == 2
        first_effect = effect_list = vertex_lists[0]
        effect_colors = effect_list.colors
    else:
        first_effect = vertex_lists[1]
        last_effect = vertex_lists[-1]
        effect_colors = last_effect.colors
    assert tuple(first_effect.colors[:8]) == gradient.start * 2
    assert tuple(effect_colors[-8:]) == gradient.end * 2


@pytest.mark.parametrize("style_name", ["background_color", "underline", "strikethrough"])
def test_decoration_style_does_not_leak_to_earlier_text(test_window, style_name):
    document = FormattedDocument("aaaaaaaa")
    document.set_style(4, 8, {style_name: (1, 2, 3, 255)})

    label = DocumentLabel(document)
    decoration_list = label._boxes[0].vertex_lists[1]  # noqa: SLF001

    assert len(label._boxes[0].vertex_lists) == 2  # noqa: SLF001
    assert decoration_list.position[0] > 0
    assert tuple(decoration_list.colors[:4]) == (1, 2, 3, 255)


def test_stroke_style_does_not_leak_to_earlier_text(test_window):
    document = FormattedDocument("aaaaaaaa")
    document.set_style(4, 8, {"stroke": Stroke(color=(1, 2, 3, 255))})

    label = DocumentLabel(document)
    vertex_lists = label._boxes[0].vertex_lists  # noqa: SLF001

    assert len(vertex_lists) == 5
    assert all(tuple(vertex_list.colors[:4]) == (1, 2, 3, 255) for vertex_list in vertex_lists[1:])
    assert vertex_lists[1].position[0] > vertex_lists[0].position[0]


def test_shadow_style_does_not_leak_to_earlier_text(test_window):
    document = FormattedDocument("aaaaaaaa")
    document.set_style(4, 8, {"shadow": DropShadow(color=(1, 2, 3, 255))})

    label = DocumentLabel(document)
    shadow_list = label._boxes[0].vertex_lists[0]  # noqa: SLF001

    assert len(label._boxes[0].vertex_lists) == 2  # noqa: SLF001
    assert tuple(shadow_list.colors[:64]) == (0, 0, 0, 0) * 16
    assert tuple(shadow_list.colors[64:68]) == (1, 2, 3, 255)


def test_shadow_uses_separate_vertex_list_with_effect_shader(test_window):
    label = Label(
        "Shadow",
        shadow=DropShadow(),
        effect_shader=get_default_layout_shader(),
    )

    assert len(label._boxes[0].vertex_lists) == 2  # noqa: SLF001


def test_shadow_uses_glyph_group_without_effect_shader(test_window):
    label = Label("Shadow", shadow=DropShadow())
    vertex_lists = label._boxes[0].vertex_lists  # noqa: SLF001

    assert vertex_lists[0].group is vertex_lists[1].group


def test_shadow_and_stroke_use_layered_groups_without_effect_shader(test_window):
    label = Label("A", shadow=DropShadow(), stroke=Stroke())
    vertex_lists = label._boxes[0].vertex_lists  # noqa: SLF001

    assert vertex_lists[1].group is vertex_lists[2].group
    assert vertex_lists[1].group.order == 0.5
    assert vertex_lists[0].group.order == 1


def test_solid_color_update_uses_fresh_style_iterator(test_window):
    document = FormattedDocument("aaaaaaaa")
    document.set_style(4, 8, {"color": (0, 0, 255, 255)})
    label = DocumentLabel(document)

    document.set_style(0, 4, {"color": (255, 0, 0, 255)})
    colors = tuple(label._boxes[0]._glyph_vertex_list.colors)  # noqa: SLF001

    assert colors[:64] == (255, 0, 0, 255) * 16
    assert colors[64:] == (0, 0, 255, 255) * 16
