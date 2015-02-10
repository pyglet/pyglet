#!/usr/bin/env python

'''Test that the code snippets mentioned in issue 471
(and related issues 241 and 429) don't have exceptions.

(Most of them delete all text in a formatted document
with some styles set; one of them (like the test in EMPTY_BOLD.py)
sets style on a 0-length range of text in an empty document.)
'''

__docformat__ = 'restructuredtext'

__noninteractive = True

import unittest

import pyglet

class TestCase(unittest.TestCase):

    def test_issue471(self):
        doc = pyglet.text.document.FormattedDocument()
        layout = pyglet.text.layout.IncrementalTextLayout(doc, 100, 100)
        doc.insert_text(0, "hello", {'bold': True})
        doc.text = ""

    def test_issue471_comment2(self):
        doc2 = pyglet.text.decode_attributed('{bold True}a')
        layout = pyglet.text.layout.IncrementalTextLayout(doc2, 100, 10)
        layout.document.delete_text(0, len(layout.document.text))

    def test_issue241_comment4a(self):
        document = pyglet.text.document.FormattedDocument("")
        layout = pyglet.text.layout.IncrementalTextLayout(document, 50, 50)
        document.set_style(0, len(document.text), {"font_name": "Arial"})

    def test_issue241_comment4b(self):
        document = pyglet.text.document.FormattedDocument("test")
        layout = pyglet.text.layout.IncrementalTextLayout(document, 50, 50)
        document.set_style(0, len(document.text), {"font_name": "Arial"})
        document.delete_text(0, len(document.text))

    def test_issue241_comment5(self):
        document = pyglet.text.document.FormattedDocument('A')
        document.set_style(0, 1, dict(bold=True))
        layout = pyglet.text.layout.IncrementalTextLayout(document,100,100)
        document.delete_text(0,1)

    def test_issue429_comment4a(self):
        doc = pyglet.text.decode_attributed('{bold True}Hello{bold False}\n\n\n\n')
        doc2 = pyglet.text.decode_attributed('{bold True}Goodbye{bold False}\n\n\n\n')
        layout = pyglet.text.layout.IncrementalTextLayout(doc, 100, 10)
        layout.document = doc2
        layout.document.delete_text(0, len(layout.document.text))

    def test_issue429_comment4b(self):
        doc2 = pyglet.text.decode_attributed('{bold True}a{bold False}b')
        layout = pyglet.text.layout.IncrementalTextLayout(doc2, 100, 10)
        layout.document.delete_text(0, len(layout.document.text))

if __name__ == '__main__':
    unittest.main()
