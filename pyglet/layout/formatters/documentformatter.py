#!/usr/bin/env python

'''Abstract formatter for marked-up documents with one or more stylesheets.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import re

from pyglet.layout.base import *
from pyglet.layout.css import SelectableElement, parse_style_declaration_set
from pyglet.layout.properties import apply_inherited_style, apply_stylesheet 
from pyglet.layout.properties import StyleTree

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
        self.boxes = []
        self.children = []
        self.computed_properties = {}

    def get_computed_property(self, property):
        return self.style_context.get_computed_property(property, self)

class DocumentFormatter(Formatter):
    '''Formatter for creating CSS boxes from element-based markup.

    This is the base class for XML, XHTML and HTML formatters.  It contains
    utility methods for processing according to the CSS whitespace model and
    implements anonymous boxes for meeting the CSS constraints.
    '''

    def __init__(self, render_device):
        super(DocumentFormatter, self).__init__(render_device)
        self.stylesheets = []
        self.style_tree = StyleTree(render_device)

    def add_stylesheet(self, stylesheet):
        '''Add the given stylesheet to this formatter.  Stylesheets are
        applied in the order that they are added, so higher-priority
        stylesheets should be added last.
        '''
        self.stylesheets.append(stylesheet)

    def create_box(self, element):
        '''Create a box for the given element.

        This checks for a matching registered box generator and invokes it,
        otherwise returns a plain Box with initial values.  Do not use this
        method to create text boxes.
        '''
        if element.name in self.generators:
            box = self.generators[element.name].create_box(
                element.name, element.attributes)
        else:
            box = Box()

        # Back-reference to elem used for interactive applications
        element.boxes.append(box)
        box.element = element
        self.apply_style(box)
        return box

    def apply_style(self,  box):
        '''Apply all styling to the given box.  
        
        Applies inherited style then the attached stylesheets in order.
        Default values and computed values are not resolved here.

        Assumes box has an 'elem' attribute which is used to apply stylesheet
        rules.
        '''
        #apply_inherited_style(box)

        #for stylesheet in self.stylesheets:
        #    apply_stylesheet(stylesheet, box.element, box, self.render_device)

        element = box.element
        if not hasattr(element, 'style_context'):
            if element.parent:
                element.parent.children.append(element)
            
            declaration_sets = []
            for stylesheet in self.stylesheets:
                declaration_sets += stylesheet.get_element_declaration_sets(element)
            if element.style:
                declaration_sets.append(parse_style_declaration_set(element.style))
            element.style_context = self.style_tree.get_style_node(declaration_sets)


        e = element
        box.margin_top = e.get_computed_property('margin_top'.replace('_', '-'))
        box.margin_bottom = e.get_computed_property('margin_bottom'.replace('_', '-'))
        box.margin_right = e.get_computed_property('margin_right'.replace('_', '-'))
        box.margin_left = e.get_computed_property('margin_left'.replace('_', '-'))
        box.padding_top = e.get_computed_property('padding_top'.replace('_', '-'))
        box.padding_bottom = e.get_computed_property('padding_bottom'.replace('_', '-'))
        box.padding_right = e.get_computed_property('padding_right'.replace('_', '-'))
        box.padding_left = e.get_computed_property('padding_left'.replace('_', '-'))
        box.border_top_width = e.get_computed_property('border_top_width'.replace('_', '-'))
        box.border_right_width = e.get_computed_property('border_right_width'.replace('_', '-'))
        box.border_bottom_width = e.get_computed_property('border_bottom_width'.replace('_', '-'))
        box.border_left_width = e.get_computed_property('border_left_width'.replace('_', '-'))
        box.border_top_color = e.get_computed_property('border_top_color'.replace('_', '-'))
        box.border_right_color = e.get_computed_property('border_right_color'.replace('_', '-'))
        box.border_bottom_color = e.get_computed_property('border_bottom_color'.replace('_', '-'))
        box.border_left_color = e.get_computed_property('border_left_color'.replace('_', '-'))
        box.border_top_style = e.get_computed_property('border_top_style'.replace('_', '-'))
        box.border_right_style = e.get_computed_property('border_right_style'.replace('_', '-'))
        box.border_bottom_style = e.get_computed_property('border_bottom_style'.replace('_', '-'))
        box.border_left_style = e.get_computed_property('border_left_style'.replace('_', '-'))
        box.display = e.get_computed_property('display'.replace('_', '-'))
        box.position = e.get_computed_property('position'.replace('_', '-'))
        box.top = e.get_computed_property('top'.replace('_', '-'))
        box.right = e.get_computed_property('right'.replace('_', '-'))
        box.bottom = e.get_computed_property('bottom'.replace('_', '-'))
        box.left = e.get_computed_property('left'.replace('_', '-'))
        box.float = e.get_computed_property('float'.replace('_', '-'))
        box.clear = e.get_computed_property('clear'.replace('_', '-'))
        box.z_index = e.get_computed_property('z_index'.replace('_', '-'))
        box.direction = e.get_computed_property('direction'.replace('_', '-'))
        box.unicode_bidi = e.get_computed_property('unicode_bidi'.replace('_', '-'))
        box.width = e.get_computed_property('width'.replace('_', '-'))
        box.min_width = e.get_computed_property('min_width'.replace('_', '-'))
        box.max_width = e.get_computed_property('max_width'.replace('_', '-'))
        box.height = e.get_computed_property('height'.replace('_', '-'))
        box.min_height = e.get_computed_property('min_height'.replace('_', '-'))
        box.max_height = e.get_computed_property('max_height'.replace('_', '-'))
        box.line_height = e.get_computed_property('line_height'.replace('_', '-'))
        box.overflow = e.get_computed_property('overflow'.replace('_', '-'))
        box.clip = e.get_computed_property('clip'.replace('_', '-'))
        box.visibility = e.get_computed_property('visibility'.replace('_', '-'))
        box.vertical_align = e.get_computed_property('vertical_align'.replace('_', '-'))

        box.list_style_image = e.get_computed_property('list_style_image'.replace('_', '-'))
        box.list_style_position = e.get_computed_property('list_style_position'.replace('_', '-'))


        box.color = e.get_computed_property('color'.replace('_', '-'))
        box.background_color = e.get_computed_property('background_color'.replace('_', '-'))
        box.background_image = e.get_computed_property('background_image'.replace('_', '-'))
        box.background_repeat = e.get_computed_property('background_repeat'.replace('_', '-'))
        box.background_attachment = e.get_computed_property('background_attachment'.replace('_', '-'))
        box.background_position = e.get_computed_property('background_position'.replace('_', '-'))

        box.font_family = e.get_computed_property('font_family'.replace('_', '-'))
        box.font_style = e.get_computed_property('font_style'.replace('_', '-'))
        box.font_variant = e.get_computed_property('font_variant'.replace('_', '-'))
        box.font_weight = e.get_computed_property('font_weight'.replace('_', '-'))
        box.font_size = e.get_computed_property('font_size'.replace('_', '-'))

        box.font = e.get_computed_property('--font')

        box.text_indent = e.get_computed_property('text_indent'.replace('_', '-'))
        box.text_align = e.get_computed_property('text_align'.replace('_', '-'))
        box.text_decoration = e.get_computed_property('text_decoration'.replace('_', '-'))
        box.letter_spacing = e.get_computed_property('letter_spacing'.replace('_', '-'))
        box.word_spacing = e.get_computed_property('word_spacing'.replace('_', '-'))
        box.text_transform = e.get_computed_property('text_transform'.replace('_', '-'))
        box.white_space = e.get_computed_property('white_space'.replace('_', '-'))

        box.caption_side = e.get_computed_property('caption_side'.replace('_', '-'))
        box.table_layout = e.get_computed_property('table_layout'.replace('_', '-'))
        box.border_collapse = e.get_computed_property('border_collapse'.replace('_', '-'))
        box.border_spacing = e.get_computed_property('border_spacing'.replace('_', '-'))
        box.empty_cells = e.get_computed_property('empty_cells'.replace('_', '-'))


    def resolve_style_defaults(self, box):
        pass

    def resolve_computed_values(self, box):
        pass
        
    def anonymous_block_box(self, boxes, parent):
        '''Create an anonymous block box to contain 'boxes' and return it.
        
        Assumes 'boxes' are inline elements.
        '''
        if parent.children:
            sib = parent.children[-1].element
        else:
            sib = None
        anon_elem = DocumentElement('(anon)', {}, parent.element, sib)

        anon = Box()
        anon.children = boxes
        anon.parent = parent
        anon.element = anon_elem
        self.apply_style(anon)
        anon.display = Ident('block') # HACK(ier)

        for box in boxes:
            assert box.display == 'inline'
            box.parent = anon
            box.element.parent = anon_elem
            box.element.previous_sibling = None
        return anon

    def anonymous_inline_box(self, text, parent):
        '''Create an anonymous inline box to contain 'text' and return it.
        '''
        if parent.children:
            sib = parent.children[-1].element
        else:
            sib = None
        anon_elem = DocumentElement('(anon)', {}, parent.element, sib)

        anon = Box()
        anon.text = text
        anon.parent = parent
        anon.element = anon_elem
        self.apply_style(anon)
        return anon

    def add_child(self, box):
        '''Add box its parent box, creating anonymous boxes as necessary.'''
        parent = box.parent
        if parent.text:
            # Anonymous inline box the existing text before continuing
            assert not parent.children
            anon = self.anonymous_inline_box(parent.text, parent)
            del parent.text
            self.add_child(anon)

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
                box = self.anonymous_block_box([box], parent)
                box.anonymous = 'True' 

        elif (box.display == 'block' and 
              parent.inline_formatting_context):
             # Convert parent to block formatting context, create
             # an anonymous block box for all existing children
             parent.inline_formatting_context = False
             if parent.children:
                parent.children = \
                    [self.anonymous_block_box(parent.children, parent)]

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
            if parent.children or parent.display != 'inline':  # TODO
                box = self.anonymous_inline_box(content, parent)
                self.add_child(box)
            else:
                parent.text += content
