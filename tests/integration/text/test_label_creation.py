"""Test creation of all Label classes and decoders"""
import random

import pytest


from pyglet.text import decode_text, decode_attributed, decode_html
from pyglet.text import Label, DocumentLabel, HTMLLabel

WIDTH = 500
HEIGHT = 100
X = random.randint(0, 900)
Y = random.randint(0, 600)
Z = random.randint(-10, 10)


@pytest.mark.parametrize('label_class', [Label, HTMLLabel])
def test_label_creation(label_class):
    label = label_class("This is a test", x=X, y=Y, z=Z)
    assert label.x == X
    assert label.y == Y
    assert label.z == Z


@pytest.fixture(params=[(decode_text, "This is a string of regular text."),
                        (decode_html, "<font color=green>This is html text.</font>"),
                        (decode_attributed, "This is {bold True}attributed{bold False} text.")])
def document(request):
    decoder, string = request.param
    return decoder(string)


def test_documentlabel_creation(document):
    label = DocumentLabel(document=document, x=X, y=Y, z=Z)
    assert label.x == X
    assert label.y == Y
    assert label.z == Z
