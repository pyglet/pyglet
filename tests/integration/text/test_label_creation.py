"""Test creation of all Label classes and decoders"""
import random

import pytest


from pyglet.text import decode_text, decode_attributed, decode_html, DropShadow, LinearGradient, Stroke
from pyglet.text.document import FormattedDocument
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
    effect_lists = vertex_lists[:-1] if style_name == "shadow" else vertex_lists[1:]
    assert tuple(effect_lists[0].colors[:8]) == gradient.start * 2
    assert tuple(effect_lists[-1].colors[-8:]) == gradient.end * 2


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


def test_solid_color_update_uses_fresh_style_iterator(test_window):
    document = FormattedDocument("aaaaaaaa")
    document.set_style(4, 8, {"color": (0, 0, 255, 255)})
    label = DocumentLabel(document)

    document.set_style(0, 4, {"color": (255, 0, 0, 255)})
    colors = tuple(label._boxes[0]._glyph_vertex_list.colors)  # noqa: SLF001

    assert colors[:64] == (255, 0, 0, 255) * 16
    assert colors[64:] == (0, 0, 255, 255) * 16
