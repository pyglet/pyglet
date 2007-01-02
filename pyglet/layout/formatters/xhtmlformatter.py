#!/usr/bin/env python

'''Formatter for XHTML markup.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.layout.css import Stylesheet
from pyglet.layout.formatters.xmlformatter import *
from pyglet.layout.formatters.htmlformatter import html4_default_stylesheet

class XHTMLElement(XMLElement):
    '''Element type for XHTML.

    Extends the XML element type by adding the 'class' and 'style' attributes.
    '''
    def __init__(self, name, attrs, parent, previous_sibling):
        super(XHTMLElement, self).__init__(name, attrs, parent, previous_sibling)
        if attrs.has_key('class'):
            self.classes = attrs['class'].split()
        if attrs.has_key('style'):
            self.style = attrs['style']

class XHTMLFormatter(XMLFormatter):
    '''Formatter for creating CSS boxes from XHTML documents, using a SAX
    parser.

    Currently the addition to XML is:
      * Add the HTML4 default stylesheet before any other.
      * Add the contents of the <style> element, if any, to a highest-priority
        stylesheet
      * Use the XHTMLElement type instead of XMLElement, which adds the
        'class' attribute
      * Apply CSS declarations to elements contained in the optional 'style'
        attribute.

    This is not complete XHTML support by far.
    '''
    element_class = XHTMLElement

    def __init__(self, render_device, locator):
        super(XHTMLFormatter, self).__init__(render_device, locator)
        self.add_stylesheet(html4_default_stylesheet)
        self.in_head = False

    def startElement(self, name, attrs):
        if name == 'head':
            self.process_content_buffer()
            self.in_head = True
        elif self.in_head and name == 'style':
            self.content_buffer = ''
        
        if not self.in_head:
            super(XHTMLFormatter, self).startElement(name, attrs)

    def endElement(self, name):
        if name == 'head':
            self.in_head = False
            self.content_buffer = ''
        elif self.in_head and name == 'style':
            stylesheet = Stylesheet(self.content_buffer)
            self.add_stylesheet(stylesheet)
            self.content_buffer = ''
        elif not self.in_head:
            super(XHTMLFormatter, self).endElement(name)
