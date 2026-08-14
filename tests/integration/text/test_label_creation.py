"""Test creation of all Label classes and decoders"""
import random

import pytest


from pyglet.text import decode_text, decode_attributed, decode_html, LinearGradient
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
