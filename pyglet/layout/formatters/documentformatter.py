#!/usr/bin/env python

'''Abstract formatter for marked-up documents with one or more stylesheets.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import re

from pyglet.layout.base import *
from pyglet.layout.css import SelectableElement
from pyglet.layout.properties import apply_inherited_style, apply_stylesheet 

class DocumentElement(SelectableElement):
    '''Default element type for element-based markup.  
    
    The ID and CLASS attributes are assumed to be empty (as these depend on
    the application).
    '''
    def __init__(self, name, attrs, parent, previous_sibling):
        self.name = name
        self.attributes = {}
        self.attributes.update(attrs)
        self.parent = parent
        self.previous_sibling = previous_sibling

class DocumentFormatter(Formatter):
    '''Formatter for creating CSS boxes from element-based markup.

    This is the base class for XML, XHTML and HTML formatters.  It contains
    utility methods for processing according to the CSS whitespace model and
    implements anonymous boxes for meeting the CSS constraints.
    '''

    def __init__(self, render_device):
        super(DocumentFormatter, self).__init__(render_device)
        self.stylesheets = []

    def add_stylesheet(self, stylesheet):
        '''Add the given stylesheet to this formatter.  Stylesheets are
        applied in the order that they are added, so higher-priority
        stylesheets should be added last.
        '''
        self.stylesheets.append(stylesheet)

    def create_box(self, elem):
        '''Create a box for the given element.

        This checks for a matching registered box generator and invokes it,
        otherwise returns a plain Box with initial values.  Do not use this
        method to create text boxes.
        '''
        if elem.name in self.generators:
            box = self.generators[elem.name].create_box(
                elem.name, elem.attributes)
        else:
            box = Box()

        # Back-reference to elem used for interactive applications
        box.elem = elem
        return box

    def apply_style(self,  box):
        '''Apply all styling to the given box.  
        
        Applies inherited style then the attached stylesheets in order.
        Default values and computed values are not resolved here.

        Assumes box has an 'elem' attribute which is used to apply stylesheet
        rules.
        '''
        apply_inherited_style(box)

        for stylesheet in self.stylesheets:
            apply_stylesheet(stylesheet, box.elem, box, self.render_device)

    def resolve_style_defaults(self, box):
        '''Apply defaults that couldn't be set with initial values.

        Specifically, these are the border width and border color properties,
        which depend on other values.  This method must be called after all
        style has been calculated, but before computed values are resolved.
        '''
        if box.border_top_style == 'none':
            box.border_top_width = 0
        if box.border_right_style == 'none':
            box.border_right_width = 0
        if box.border_bottom_style == 'none':
            box.border_bottom_width = 0
        if box.border_left_style == 'none':
            box.border_left_width = 0

        if box.border_top_color is None and box.border_top_width != 0:
            box.border_top_color = box.color
        if box.border_right_color is None and box.border_right_width != 0:
            box.border_right_color = box.color
        if box.border_bottom_color is None and box.border_bottom_width != 0:
            box.border_bottom_color = box.color
        if box.border_left_color is None and box.border_left_width != 0:
            box.border_left_color = box.color

    # Attributes with computed length.  This list may not yet be complete.  
    _length_attribute_names = set(
       ['margin_top', 'margin_right', 'margin_bottom', 'margin_left',
       'padding_top', 'padding_right', 'padding_bottom', 'padding_left',
       'border_top_width', 'border_right_width', 'border_bottom_width',
       'border_left_width', 'top', 'right', 'bottom', 'left', 'width',
       'min_width', 'max_width', 'height', 'min_height', 'max_height',
       'line_height', 'text_indent', 'letter_spacing', 'word_spacing',
       'border_spacing',
       'intrinsic_width', 'intrinsic_height'])

    def resolve_computed_values(self, box):
        '''Resolve box property values to their computed values.  
        
        This includes resolving lengths that depend on the box's or parent's
        font-size and converting lengths into device units.  Some named
        values are also converted to numeric values, such as the font-weight
        property.
        '''
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

        # replaced element with no intrinsic width: 10.3.2
        if (box.is_replaced and 
            box.intrinsic_width is None and box.width == 'auto' and
            (box.intrinsic_ratio is None or 
             (box.intrinsic_height is None and box.height == 'auto'))):
            box.width = self.render_device.dimension_to_device('300px', 0)
        # replaced element with no intrinsic height: 10.6.2
        if (box.is_replaced and
            box.intrinsic_height is None and box.height == 'auto' and
            (box.intrinsic_ratio is None or
             (box.intrinsic_height is None and box.height == 'auto'))):
            box.height = self.render_device.dimension_to_device('150px', 0)
             
    def anonymous_block_box(self, boxes):
        '''Create an anonymous block box to contain 'boxes' and return it.
        
        Assumes 'boxes' are inline elements.
        '''
        anon = Box()
        apply_inherited_style(anon)
        self.resolve_style_defaults(anon)
        self.resolve_computed_values(anon)
        anon.display = Ident('block')
        anon.children = boxes
        for box in boxes:
            assert box.display == 'inline'
            box.parent = anon
        return anon

    def add_child(self, box):
        '''Add box its parent box, creating anonymous boxes as necessary.'''
        parent = box.parent
        if not parent.children:
            parent.children = []

        # 9.2.1.1 Anonymous block boxes
        if (box.display == 'inline' and
            not parent.inline_formatting_context):
            if parent.children and parent.children[-1].anonymous:
                # Can use existing anonymous box
                parent = parent.children[-1]
            else:
                # Create anonymous block box around inline box.
                box = self.anonymous_block_box([box])
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

    ws_normalize_pattern = re.compile('\r\n|\n|\r')
    ws_step1_pattern = re.compile('[ \r\t]*\n[ \r\t]*')
    ws_step2a_pattern = re.compile('( +)')
    ws_step2_pattern = re.compile(' ')
    ws_step3_pattern = re.compile('\n') 
    ws_step4a_pattern = re.compile('\t')
    ws_step4b_pattern = re.compile(' +')
    _collapse_leading_space = False

    def add_text(self, content, parent):
        '''Add the string 'content' to box 'parent'.  This method calls
        'add_child', so anonymous boxes are created automatically when
        necessary.
        
        XXX: Assumes content is given sequentially.  This is true for the
        current formatters which process elements in pre-order, but the method
        is not usable for document tree modifications.
        '''
        # Normalize newlines to \n.  This isn't part of CSS, but I think I saw
        # it somewhere in XML.  Anyway, it's needed.
        content = self.ws_normalize_pattern.sub('\n', content)

        # Collapse white-space according to 16.6.1.
        # Step 1
        if parent.white_space in ('normal', 'nowrap', 'pre-line'):
            # Remove white-space surrounding a newline
            content = self.ws_step1_pattern.sub('\n', content)

        # Step 2
        if parent.white_space in ('pre', 'pre-wrap'):
            if parent.white_space == 'pre-wrap':
                # Break opportunity after sequence of spaces
                content = self.ws_step2a_pattern.sub(u'\\1\u200b', content)
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
            font = self.render_device.get_font(parent)
            boxes = self.render_device.create_inline_text_boxes(font, content)
            for box in boxes:
                box.parent = parent
                apply_inherited_style(box)
                self.resolve_style_defaults(box)
                self.resolve_computed_values(box)
                self.add_child(box) 
