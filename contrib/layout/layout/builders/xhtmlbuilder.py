#!/usr/bin/env python

'''Build content tree from XHTML source, applying default HTML stylesheet.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from layout.content import *
from layout.css import *
from layout.builders import *
from layout.builders.xmlbuilder import *
from layout.builders.htmlstylesheet import *

__all__ = ['XHTMLElement', 'XHTMLBuilder']

class XHTMLElement(XMLElement):
    def __init__(self, document, name, attributes, parent, previous_sibling):
        super(XHTMLElement, self).__init__(
            document, name, attributes, parent, previous_sibling)
        if attributes.has_key('class'):
            self.classes = attributes['class'].lower().split()
        if attributes.has_key('style'):
            self.set_element_style(attributes['style'])

class XHTMLBuilder(XMLBuilder):
    element_class = XHTMLElement
            
    def __init__(self, document):
        super(XHTMLBuilder, self).__init__(document)
        self.document.stylesheets.append(html4_default_stylesheet)

        self.preamble_stack = []
        self.preamble = False
        self.buffer = ''

    def begin_element(self, name, attributes):
        if name == 'head':
            self.preamble = True

        if self.preamble:
            self.preamble_stack.append(name)
            self.buffer = ''
        else:
            super(XHTMLBuilder, self).begin_element(name, attributes)

    def end_element(self, name):
        if not self.preamble:
            super(XHTMLBuilder, self).end_element(name)
        else:
            self.preamble_stack.pop()
            if name == 'style':
                self.document.stylesheets.append(Stylesheet(self.buffer))
            elif name == 'title':
                self.document.title = self.buffer

        if name == 'head':
            self.preamble = False

    def text(self, text):
        if not self.preamble:
            super(XHTMLBuilder, self).text(text)
        else:
            self.buffer += text
