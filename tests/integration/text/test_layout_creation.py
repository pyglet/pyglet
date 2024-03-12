"""Test creation of all Layout classes"""
import random
import itertools


import pytest

from pyglet.text import document
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
def test_layout_creation_keyword(doctype, layouttype):
    _doc = doctype("This is a test")
    _layout = layouttype(document=_doc, x=X, y=Y, z=Z, width=WIDTH, height=HEIGHT)
    assert _layout.x == X
    assert _layout.y == Y
    assert _layout.z == Z
    assert _layout.width == WIDTH
    assert _layout.height == HEIGHT
    assert _layout.position == (X, Y, Z)


@pytest.mark.parametrize('doctype, layouttype', all_combinations)
def test_layout_creation_positional(doctype, layouttype):
    _doc = doctype("This is a test")
    _layout = layouttype(_doc, X, Y, Z, WIDTH, HEIGHT)
    # Make sure the arguments were in order:
    assert _layout.x == X
    assert _layout.y == Y
    assert _layout.z == Z
    assert _layout.width == WIDTH
    assert _layout.height == HEIGHT
    assert _layout.position == (X, Y, Z)
