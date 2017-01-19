#!/usr/bin/env python

'''Test content tree construction from HTML source.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from layout.content import *
from layout.builders.htmlbuilder import *

class HTMLBuilderTest(unittest.TestCase):
    def check(self, test, expected):
        document = Document()
        builder = HTMLBuilder(document)
        builder.feed(test)
        builder.close()
        result = self.canonical(document.root)
        self.assertTrue(result == expected, 
            'Result:\n%s\nExpected:\n%s\n' % (result, expected))

    def canonical(self, element):
        can = ''
        if not element.is_anonymous:
            can += '<%s>' % element.name
        for child in element.children:
            can += self.canonical(child)
        if element.text:
            can += element.text.strip()
        if not element.is_anonymous:
            can += '</%s>' % element.name
        return can
        
    def test_sanity(self):
        self.check(
   '<html><body><p>Hello</p></body></html>',
   '<html><body><p>Hello</p></body></html>')

    def test_noopen_html(self):
        self.check(
   '<head><title>Goodbye</title></head><body><p>Hello</p></body></html>',
   '<html><body><p>Hello</p></body></html>')

    def test_noopen_head(self):
        self.check(
   '<title>Goodbye</title></head><body><p>Hello</p></body></html>',
   '<html><body><p>Hello</p></body></html>')

    def test_noopen_body(self):
        self.check(
   '<title>Goodbye</title></head><p>Hello</p></body></html>',
   '<html><body><p>Hello</p></body></html>')

    def test_noclose_html(self):
        self.check(
   '<html><head><title>Goodbye</title></head><body><p>Hello</p></body>',
   '<html><body><p>Hello</p></body></html>')

    def test_noclose_head(self):
        self.check(
   '<html><head><title>Goodbye</title><body><p>Hello</p></body>',
   '<html><body><p>Hello</p></body></html>')

    def test_noclose_title(self):
        self.check(
   '<html><head><title>Goodbye</head><body><p>Hello</p></body>',
   '<html><body><p>Hello</p></body></html>')

    def test_noclose_any(self):
        self.check(
   '<html><head><title>Goodbye<body><p>Hello',
   '<html><body><p>Hello</p></body></html>')

    def test_minimal(self):
        self.check(
   '<title>Goodbye<p>Hello',
   '<html><body><p>Hello</p></body></html>')

    def test_zen(self):
        self.check(
   'Hello',
   '<html><body>Hello</body></html>')

    def test_p(self):
        self.check(
   '<p>Para1<p>Para2<p>Para3',
   '<html><body><p>Para1</p><p>Para2</p><p>Para3</p></body></html>')

    def test_nest_div_p(self):
        self.check(
   '<div><p>Para1<div><p>Para2',
   '<html><body><div><p>Para1<div><p>Para2</p></div></p></div></body></html>')

    def test_ul_li(self):
        self.check(
   '<ul><li>One<li>Two<li>Three</ul>',
   '<html><body><ul><li>One</li><li>Two</li><li>Three</li></ul></body></html>')


if __name__ == '__main__':
    unittest.main()
