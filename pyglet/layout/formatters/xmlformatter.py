#!/usr/bin/env python

'''Format XML markup into CSS boxes.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import xml.sax

from pyglet.layout.base import *
from pyglet.layout.formatters.documentformatter import *

class XMLElement(DocumentElement):
    '''Element type for XML markup.

    Currently the ID attribute is taken from the 'id' attribute, which isn't
    necessarily correct (a DTD can change the name of the ID attribute).

    There is no CLASS attribute.
    '''
    def __init__(self, name, attrs, parent, previous_sibling):
        super(XMLElement, self).__init__(name, attrs, parent, previous_sibling)
        # TODO: find id attr(s) from DTD. 
        if attrs.has_key('id'):
            self.id = attrs['id']

class XMLFormatter(DocumentFormatter):
    '''Formatter for creating CSS boxes from XML using a SAX parser.
    '''
    element_class = XMLElement

    def __init__(self, render_device, locator):
        super(XMLFormatter, self).__init__(render_device)
        self.locator = locator

    def format(self, data):
        if hasattr(data, 'read'):
            xml.sax.parse(data, self)
        else:
            xml.sax.parseString(data, self)
        return self.root_box

    # xml.sax ContentHandler methods
    # ------------------------------

    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        self.box_stack = []
        self.element_stack = []
        self.element_sibling_stack = [None]
        self.root_box = None
        self.content_buffer = ''

    def endDocument(self):
        pass

    def startPrefixMapping(self, prefix, uri):
        pass

    def endPrefixMapping(self, prefix):
        pass

    def startElement(self, name, attrs):
        self.process_content_buffer()

        if not self.root_box:
            elem = self.element_class(name, attrs, None, None)
            box = self.create_box(elem)
            self.root_box = box
        else:
            elem = self.element_class(name, attrs, 
                self.element_stack[-1], self.element_sibling_stack.pop())
            self.element_sibling_stack.append(elem)
            box = self.create_box(elem)
            box.parent = self.box_stack[-1]

        self.apply_style(box)
        self.resolve_style_defaults(box)
        self.resolve_computed_values(box)

        if box.parent:
            self.add_child(box)
        self.box_stack.append(box)
        self.element_stack.append(elem)
        self.element_sibling_stack.append(None)

    def endElement(self, name):
        self.process_content_buffer()

        # TODO Resolve run-in elements.
        self.box_stack.pop()        
        self.element_stack.pop()
        self.element_sibling_stack.pop()

    def startElementNS(self, name, qname, attrs):
        raise NotImplementedError('Unhandled: startElementNS')

    def endElementNS(self, name, qname):
        pass

    def characters(self, content):
        # Rather than add inline boxes directly, wait until all content
        # is in (SAX parsers split every newline) -- reduces number of
        # boxes.
        self.content_buffer += content

    def process_content_buffer(self):
        content = self.content_buffer
        self.content_buffer = ''

        # Ignore text (white-space) before root element.
        if not self.box_stack:
            return
        self.add_text(content, self.box_stack[-1])

    def ignorableWhitespace(self, whitespace):
        pass

    def processingInstruction(self, target, data):
        pass

    def skippedEntity(self, name):
        pass

