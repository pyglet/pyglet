"""Test creation of all Layout classes"""
import random
import itertools
import unittest

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
def test_layout_creation_keyword(gl3_context, doctype, layouttype):
    _doc = doctype("This is a test")
    _layout = layouttype(document=_doc, x=X, y=Y, z=Z, width=WIDTH, height=HEIGHT)
    assert _layout.x == X
    assert _layout.y == Y
    assert _layout.z == Z
    assert _layout.width == WIDTH
    assert _layout.height == HEIGHT
    assert _layout.position == (X, Y, Z)


@pytest.mark.parametrize('doctype, layouttype', all_combinations)
def test_layout_creation_positional(gl3_context, doctype, layouttype):
    _doc = doctype("This is a test")
    _layout = layouttype(_doc, X, Y, Z, WIDTH, HEIGHT)
    # Make sure the arguments were in order:
    assert _layout.x == X
    assert _layout.y == Y
    assert _layout.z == Z
    assert _layout.width == WIDTH
    assert _layout.height == HEIGHT
    assert _layout.position == (X, Y, Z)


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
        doc = decode_attributed(
            '{bold True}Hello{bold False}\n\n\n\n')
        doc2 = decode_attributed(
            '{bold True}Goodbye{bold False}\n\n\n\n')
        incremental_layout = layout.IncrementalTextLayout(doc, 100, 10, width=500, height=100)
        incremental_layout.document = doc2
        incremental_layout.document.delete_text(0, len(incremental_layout.document.text))

    def test_issue429_comment4b(self):
        doc2 = decode_attributed('{bold True}a{bold False}b')
        incremental_layout = layout.IncrementalTextLayout(doc2, 100, 10, width=500, height=100)
        incremental_layout.document.delete_text(0, len(incremental_layout.document.text))

def test_incrementallayout_get_position_on_line_before_start_of_text(gl3_context):
    single_line_text = "This is a single line of text."
    doc = document.UnformattedDocument(single_line_text)
    font = doc.get_font()
    incremental_layout = layout.IncrementalTextLayout(doc,
                                                      height = font.ascent - font.descent,
                                                      width = 200,
                                                      multiline=False)
    incremental_layout.x = 100
    incremental_layout.y = 100

    assert incremental_layout.get_position_on_line(0, 100) == 0
    assert incremental_layout.get_position_on_line(0, 90) == 0
    assert incremental_layout.get_position_on_line(0, 80) == 0
    assert incremental_layout.get_position_on_line(0, 70) == 0
    assert incremental_layout.get_position_on_line(0, 60) == 0
    assert incremental_layout.get_position_on_line(0, 50) == 0