#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import re
import xml.sax

from pyglet.layout.base import *
import pyglet.layout.visual
from pyglet.layout.css import apply_style_string, apply_inherited_style, apply_stylesheet

class XMLElement(pyglet.layout.css.SelectableElement):
    def __init__(self, name, attrs, parent, previous_sibling):
        self.name = name
        # TODO Gross assumption; should check DTD for id attr
        if attrs.has_key('id'):
            self.id = attrs['id']
        # TODO move to XHTML
        if attrs.has_key('class'):
            self.classes = attrs['class'].split()
        self.attributes = {}
        self.attributes.update(attrs)
        self.parent = parent
        self.previous_sibling = previous_sibling


class XMLFormatter(pyglet.layout.visual.Formatter):
    def __init__(self, render_device):
        super(XMLFormatter, self).__init__(render_device)

        self.stylesheets = []

    def format(self, data):
        if hasattr(data, 'read'):
            xml.sax.parse(data, self)
        else:
            xml.sax.parseString(data, self)
        return self.root_box

    def add_stylesheet(self, stylesheet):
        self.stylesheets.append(stylesheet)

    def create_box(self, name, attrs):
        if name in self.generators:
            return self.generators[name].create_box(name, attrs)
        return Box()

    def apply_style(self,  box, elem):
        apply_inherited_style(box)

        for stylesheet in self.stylesheets:
            apply_stylesheet(stylesheet, elem, box, self.render_device)

        # TODO move style attr to XHTML/HTML only
        if 'style' in elem.attributes:
            scanner = apply_style_string(elem.attributes['style'], box, 
                self.render_device)

        self.resolve_style_defaults(box)
        self.resolve_computed_values(box)

    def resolve_style_defaults(self, box):
        # Apply defaults that couldn't be set with initial values.
        if box.border_top_style == 'none':
            box.border_top_width = 0
        if box.border_right_style == 'none':
            box.border_right_width = 0
        if box.border_bottom_style == 'none':
            box.border_bottom_width = 0
        if box.border_left_style == 'none':
            box.border_left_width = 0

        if box.border_top_color is None:
            box.border_top_color = box.color
        if box.border_right_color is None:
            box.border_right_color = box.color
        if box.border_bottom_color is None:
            box.border_bottom_color = box.color
        if box.border_left_color is None:
            box.border_left_color = box.color

    # Attributes with computed length  
    _length_attribute_names = set(
       ['margin_top', 'margin_right', 'margin_bottom', 'margin_left',
       'padding_top', 'padding_right', 'padding_bottom', 'padding_left',
       'border_top_width', 'border_right_width', 'border_bottom_width',
       'border_left_width', 'top', 'right', 'bottom', 'left', 'width',
       'min_width', 'max_width', 'height', 'min_height', 'max_height',
       'line_height', 'text_indent', 'letter_spacing', 'word_spacing',
       'border_spacing'])
    def resolve_computed_values(self, box):
        '''Resolve relative and absolute lengths to device units.'''
        # font-size first, since em and ex depend on it
        font_size = box.font_size
        if isinstance(box.font_size, Dimension):
            if font_size.unit == 'em':
                size = box.parent.font_size * font_size 
            elif font_size.unit == 'ex':
                # This is just a stupid guess, no way to calculate it
                # properly.
                size = box.parent.font_size * font_size * 0.5
            else:
                size = self.render_device.dimension_to_pt(font_size)
            font_size = Dimension('%fpt' % size) 
        elif isinstance(font_size, Ident):
            font_size = self.render_device.get_named_font_size(font_size)
        box.font_size = font_size
        font_size_device = \
            self.render_device.dimension_to_device(font_size, font_size)

        # other values that are relative to font-size
        for attrname in set(box.__dict__.keys()) & self._length_attribute_names:
            value = getattr(box, attrname)
            if isinstance(value, Dimension):
                value = self.render_device.dimension_to_device(value, font_size)
                setattr(box, attrname, value)

        # line-height percentage of font-size
        if type(box.line_height) in (Percentage, Number):
            box.line_height = font_size_device * box.line_height

        # font-weight names and relative values
        if box.font_weight == 'normal':
            box.font_weight = 400
        elif box.font_weight == 'bold':
            box.font_weight = 700
        elif box.font_weight == 'bolder':
            box.font_weight = box.parent.font_weight + 300
        elif box.font_weight == 'lighter':
            box.font_weight = box.parent.font_weight - 300

    def anonymous_block_box(self, boxes, parent):
        '''Create an anonymous block box for 'boxes' and return it.'''
        anon = Box()
        anon.parent = parent
        apply_inherited_style(anon)
        self.resolve_style_defaults(anon)
        self.resolve_computed_values(anon)
        anon.display = Ident('block')
        anon.children = boxes
        for box in boxes:
            assert box.display == 'inline'
            box.parent = anon
        return anon

    def add_child(self, box, parent):
        '''Add box to parent, creating anonymous boxes as necessary.'''
        # TODO Create generated boxes.
        if parent.children is None:
            parent.children = []

        # 9.2.1.1 Anonymous block boxes
        if (box.display == 'inline' and
            not parent.inline_formatting_context):
            if parent.children and parent.children[-1].anonymous:
                # Can use existing anonymous box
                parent = parent.children[-1]
            else:
                # Create anonymous block box around inline box.
                box = self.anonymous_block_box([box], parent)
                box.anonymous = 'True' 

        elif (box.display == 'block' and 
              parent.inline_formatting_context):
             # Convert parent to block formatting context, create
             # an anonymous block box for all existing children
             parent.inline_formatting_context = False
             if parent.children:
                parent.children = [self.anonymous_block_box(parent.children)]

        parent.children.append(box)
        box.parent = parent

    # xml.sax ContentHandler methods
    # ------------------------------

    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        self.box_stack = []
        self.element_stack = []
        self.element_sibling_stack = [None]
        self.root_box = None

    def endDocument(self):
        pass

    def startPrefixMapping(self, prefix, uri):
        pass

    def endPrefixMapping(self, prefix):
        pass

    def startElement(self, name, attrs):
        self.process_content_buffer()

        box = self.create_box(name, attrs)
        if not self.root_box:
            elem = XMLElement(name, attrs, None, None)
            self.apply_style(box, elem)
            self.root_box = box
        else:
            elem = XMLElement(name, attrs, 
                self.element_stack[-1], self.element_sibling_stack.pop())
            self.element_sibling_stack.append(elem)

            box.parent = self.box_stack[-1]
            self.apply_style(box, elem)
            self.add_child(box, box.parent)
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

    ws_step1_pattern = re.compile('[ \r\t]*\n[ \r\t]*')
    ws_step2a_pattern = re.compile('( +)')
    ws_step2_pattern = re.compile(' ')
    ws_step3_pattern = re.compile('\n')
    ws_step4a_pattern = re.compile('\t')
    ws_step4b_pattern = re.compile(' +')
    _collapse_leading_space = False
    _content_buffer = ''

    def characters(self, content):
        # Rather than add inline boxes directly, wait until all content
        # is in (SAX parsers split every newline) -- reduces number of
        # boxes.
        self._content_buffer += content

    def process_content_buffer(self):
        content = self._content_buffer
        self._content_buffer = ''

        # Ignore text (white-space) before root element.
        if not self.box_stack:
            return
        parent = self.box_stack[-1]
        font = self.render_device.get_font(parent)

        # Collapse white-space according to 16.6.1.
        # Step 1
        if parent.white_space in ('normal', 'nowrap', 'pre-line'):
            # Remove white-space surrounding a newline
            content = self.ws_step1_pattern.sub('\n', content)

        # Step 2
        if parent.white_space in ('pre', 'pre-wrap'):
            if parent.white_space == 'pre-wrap':
                # Break opportunity after sequence of spaces
                content = self.ws_step2a_pattern.sub(u'\1\u200b', content)
            # Replace spaces with non-breaking spaces
            content = self.ws_step2_pattern.sub(u'\u00a0', content)

        # Step 3
        if parent.white_space in ('normal', 'nowrap'):
            # Replace newlines with space (TODO in some scripts, use
            # zero-width space or no character)
            content = self.ws_step3_pattern.sub(' ', content) 

        # Step 4
        if parent.white_space in ('normal', 'nowrap', 'pre-line'):
            # Replace tabs with spaces
            content = self.ws_step4a_pattern.sub(' ', content)
            # Collapse consecutive spaces
            content = self.ws_step4b_pattern.sub(' ', content)
            # Remove leading space
            if self._collapse_leading_space:
                content = content.lstrip(' ')
            # Flag next text element to collapse
            if content:
                self._collapse_leading_space = content[-1] == ' '
        else:
            # Don't collapse leading WS in the next text element
            self._collapse_leading_space = False

        # Don't create anonymous block boxes when whitespace would be
        # collapsed away anyway.
        if ((not parent.inline_formatting_context or
             not parent.children) and
            parent.white_space in ('normal', 'nowrap', 'pre-line') 
            and not content.strip()):
            return

        if content:
            boxes = self.render_device.create_inline_text_boxes(font, content)
            for box in boxes:
                box.parent = parent
                apply_inherited_style(box)
                self.resolve_style_defaults(box)
                self.resolve_computed_values(box)
                self.add_child(box, parent)

    def ignorableWhitespace(self, whitespace):
        pass

    def processingInstruction(self, target, data):
        pass

    def skippedEntity(self, name):
        pass

