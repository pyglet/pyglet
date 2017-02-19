#!/usr/bin/env python

'''Build content tree from XML source.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import xml.sax

from layout.content import *
from layout.css import *
from layout.builders import *

__all__ = ['XMLElement', 'XMLBuilder']

class XMLElement(ContentElement):
    def __init__(self, document, name, attributes, parent, previous_sibling):
        super(XMLElement, self).__init__(
            document, name, attributes, parent, previous_sibling)
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

