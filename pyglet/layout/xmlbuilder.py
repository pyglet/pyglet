#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import xml.sax

from pyglet.layout.content import *
from pyglet.layout.css import *
from pyglet.layout.formatters.htmlformatter import html4_default_stylesheet

__all__ = ['XMLElement', 'XMLBuilder', 'XHTMLElement', 'XHTMLBuilder']

class XMLElement(ContentElement):
    def __init__(self, name, attributes, parent, previous_sibling):
        super(XMLElement, self).__init__(
            name, attributes, parent, previous_sibling)
        if attributes.has_key('id'):
            self.id = attributes['id']

class XMLBuilder(ContentBuilder):
    element_class = XMLElement

    def __init__(self, document):
        super(XMLBuilder, self).__init__(document)
        self.parser = xml.sax.make_parser()
        self.parser.setContentHandler(self)

    def feed(self, data):
        self.parser.feed(data)

    def close(self):
        self.parser.close()

    # xml.sax.ContentHandler interface
    # --------------------------------

    def setDocumentLocator(self, locator):
        pass

    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def startPrefixMapping(self, prefix, uri):
        pass

    def endPrefixMapping(self, prefix):
        pass

    def startElement(self, name, attrs):
        self.begin_element(name, attrs)

    def endElement(self, name):
        self.end_element(name)

    def startElementNS(self, name, qname, attrs):
        raise NotImplementedError('startElementNS')

    def endElementNS(self, name, qname):
        raise NotImplementedError('endElementNS')
        
    def characters(self, content):
        self.text(content)

    def ignorableWhitespace(self, whitespace):
        pass

    def processingInstruction(self, target, data):
        pass

    def skippedEntity(self, name):
        pass

class XHTMLElement(XMLElement):
    def __init__(self, name, attributes, parent, previous_sibling):
        super(XHTMLElement, self).__init__(
            name, attributes, parent, previous_sibling)
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
