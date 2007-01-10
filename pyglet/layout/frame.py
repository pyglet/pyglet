#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import warnings

from pyglet.layout.content import *
from pyglet.layout.properties import *

import re

__all__ = ['ContainingBlock', 'FrameBuilder', 'TextFrame']

class ContainingBlock(object):
    '''A rectangular region in which boxes are placed.  If height is None,
    the height is not explicit (dependent on content size).

    Described in 9.1.2.
    '''
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __repr__(self):
        return '%s(%dx%d)' % (self.__class__.__name__, self.width, self.height)

class Frame(object):
    # These usually remain class-level, but are sometimes overridden
    inline_level = False
    inline_context = False

    # What makes up a frame
    element = None
    parent = None
    children = ()
    text = None
    style = None
    computed_properties = None
    continuation = None

    # Bounding box, relative to the canvas (or viewport, if fixed).
    bounding_box_top = 0
    bounding_box_right = 0
    bounding_box_bottom = 0
    bounding_box_left = 0

    # Border edge, relative to parent's content area.
    border_edge_left = 0
    border_edge_top = 0
    border_edge_width = 0
    border_edge_height = 0

    # Box model used-value properties
    margin_top = 0
    margin_right = 0
    margin_bottom = 0
    margin_left = 0

    # Offset of content area relative to border edge
    content_top = 0
    content_left = 0

    def __init__(self, style, element):
        self.style = style
        self.element = element
        self.computed_properties = {}

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.element)

    def get_computed_property(self, property):
        return self.style.get_computed_property(property, self)

    # Reflow
    # ------

    def flow(self, containing_block):
        '''Flow all children, then position all children.
        '''
        raise NotImplementedError('abstract')

        # General form:
        generated_block = self.create_generated_block(width)
        for child in children:
            child.flow(generated_block.width)
            # update required space based on child size;
            # check child for continuation and add into flow.

        # update generated block to contain all children

        for child in children:
            child.position(x, y, generated_block)

        # update size of this frame

    def position(self, x, y, containing_block):
        self.border_edge_left = x
        self.border_edge_top = y
        if self.get_computed_property('position') == 'relative':
            left = self.get_computed_property('left')
            top = self.get_computed_property('top')
            if type(left) == Percentage:
                left = left * containing_block.width
            elif left == 'auto':
                left = 0
            if type(top) == Percentage:
                top = top * containing_block.height
            elif top == 'auto':
                top = 0

            self.border_edge_left += left
            self.border_edge_top += top

    # Drawing and hit-testing
    # -----------------------

    # TODO: drawing/hit-testing is currently Y+up instead of against the
    # canvas Y+down.

    def draw(self, x, y, render_device):
        '''Draw this frame with border_edge relative to given x,y.
        '''
        lx = x + self.border_edge_left
        ly = y - self.border_edge_top

        self.draw_background(lx, ly, render_device)
        self.draw_border(lx, ly, render_device)

        if self.continuation:
            self.continuation.draw(x, y, render_device)

        for child in self.children:
            child.draw(lx, ly, render_device)

    def draw_background(self, x, y, render_device):
        '''Draw the background of this frame with the border-edge top-left at
        the given coordinates.'''
        render_device.draw_background(
            x,
            y,
            x + self.border_edge_width,
            y - self.border_edge_height,
            self)

    def draw_border(self, x, y, render_device):
        '''Draw the border of this frame with the border-edge top-left at the
        given coordinates.
        
        Each border edge is drawn as a trapezoid.  The render device takes
        care of applying the border style if it is not 'none'.
        '''
        x2 = x + self.border_edge_width
        y2 = y - self.border_edge_height
        
        compute = self.get_computed_property
        btop = compute('border-top-width')
        bright = compute('border-right-width')
        bbottom = compute('border-bottom-width')
        bleft = compute('border-left-width')

        if btop:
            render_device.draw_horizontal_border(
                x + bleft, y - btop,
                x2 - bright, y - btop,
                x2, y,
                x, y, 
                compute('border-top-color'), compute('border-top-style'))
        if bright:
            render_device.draw_vertical_border(
                x2 - bright, y - btop,
                x2 - bright, y2 + bbottom,
                x2, y2,
                x2, y,
                compute('border-right-color'), compute('border-right-style'))
        if bbottom:
            render_device.draw_horizontal_border(
                x + bleft, y2 + bbottom,
                x2 - bright, y2 + bbottom,
                x2, y2,
                x, y2,
                compute('border-bottom-color'), compute('border-bottom-style'))
        if bleft:
            render_device.draw_vertical_border(
                x + bleft, y - btop,
                x + bleft, y2 + bbottom,
                x, y2,
                x, y,
                compute('border-left-color'), compute('border-left-style'))

    def resolve_bounding_box(self, x, y):
        '''Determine bounding box of this frame.

        x,y give the top-left corner of the content edge of the parent.

        The coordinates of the bounding box are relative to the canvas
        (or the viewport, for a fixed element), not the parent.
        '''

        lx = x + self.border_edge_left
        ly = y - self.border_edge_top
        self.bounding_box_left = lx
        self.bounding_box_top = ly
        self.bounding_box_right = lx + self.border_edge_width
        self.bounding_box_bottom = ly - self.border_edge_height
        if self.continuation:
            self.continuation.resolve_bounding_box(x, y)
            self.bounding_box_left = \
                min(self.bounding_box_left, self.continuation.bounding_box_left)
            self.bounding_box_right = \
                max(self.bounding_box_right, self.continuation.bounding_box_right)
            self.bounding_box_top = \
                max(self.bounding_box_top, self.continuation.bounding_box_top)
            self.bounding_box_bottom = \
                min(self.bounding_box_bottom, self.continuation.bounding_box_bottom)
        for child in self.children:
            child.resolve_bounding_box(lx, ly)
            self.bounding_box_left = \
                min(self.bounding_box_left, child.bounding_box_left)
            self.bounding_box_right = \
                max(self.bounding_box_right, child.bounding_box_right)
            self.bounding_box_top = \
                max(self.bounding_box_top, child.bounding_box_top)
            self.bounding_box_bottom = \
                min(self.bounding_box_bottom, child.bounding_box_bottom)

    def get_frames_for_point(self, x, y):
        if (x >= self.bounding_box_left and
            x < self.bounding_box_right and
            y < self.bounding_box_top and
            y >= self.bounding_box_bottom):
            frames = [self]
            for child in self.children:
                frames += child.get_frames_for_point(x, y)
            return frames
        return []

    # Debug methods
    # -------------

    def pprint(self, indent=''):
        import textwrap
        print '\n'.join(textwrap.wrap(repr(self), 
            initial_indent=indent, subsequent_indent=indent))
        for child in self.children:
            child.pprint(indent + '  ')

    def pprint_style(self, indent=''):
        import textwrap
        print '\n'.join(textwrap.wrap(repr(self), 
            initial_indent=indent, subsequent_indent=indent))
        style = self.style
        style_i = indent
        while style:
            print '\n'.join(textwrap.wrap(repr(style),
                initial_indent=style_i+'`-', subsequent_indent=style_i+'  '))
            style = style.parent
            style_i += '  '
        for child in self.children:
            child.pprint_style(indent + '  ')

class BlockFrame(Frame):
    inline_level = False
    inline_context = True       # Flips if a block-level child is added

    def create_containing_block(self, containing_block):
        '''Also sets frame metrics with the exception of 
        border_edge_height, if implicit.

        Returns generated containing block.
        '''
        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                value = value * containing_block.width
            return value
        
        # Calculate computed and used values of box properties when
        # relative to containing block width.
        content_right = computed('border-right-width') + used('padding-right')
        self.content_left = computed('border-left-width') + used('padding-left')
        self.content_top = computed('border-top-width') + used('padding-top')
        self.margin_top = used('margin-top')
        self.margin_right = used('margin-right')
        self.margin_bottom = used('margin-bottom')
        self.margin_left = used('margin-left')

        # Width and left/right margins, described in 10.3.3
        auto_margin_left = auto_margin_right = False
        if self.margin_left == 'auto':
            auto_margin_left = True
            self.margin_left = 0
        if self.margin_right == 'auto':
            auto_margin_right = True
            self.margin_right = 0
        non_content_width = self.margin_left + self.content_left + \
            content_right + self.margin_right
        remaining_width = containing_block.width - non_content_width

        # Determine content width
        content_width = computed('width')
        if content_width == 'auto':
            content_width = containing_block.width - non_content_width
        else:
            if not auto_margin_left and not auto_margin_right:
                # Over-constrained
                if computed('direction') == 'ltr':
                    auto_margin_right = True
                else:
                    auto_margin_left = True

            # Distribute remaining space over all 'auto' margins
            if auto_margin_left and auto_margin_right:
                self.margin_left = remaining_width / 2
                self.margin_right = remaining_width / 2
            elif auto_margin_left:
                self.margin_left = remaining_width
            else:
                self.margin_right = remaining_width

        # Set border_edge_width now
        self.border_edge_width = self.content_left + content_width + \
            content_right

        # Determine content height (may be auto)
        content_height = computed('height')
        if type(content_height) == Percentage:
            if containing_block.bottom is None:
                content_height = 'auto'
            else:
                content_height =  content_height * containing_block.height

        if content_height == 'auto':
            return ContainingBlock(content_width, None)
        else:
            return ContainingBlock(content_width, content_height)


    def flow(self, containing_block):
        '''Flow all children, then position all children.
        '''
        generated_containing_block = \
            self.create_containing_block(containing_block)
        if self.inline_context:
            self.flow_inline(generated_containing_block)
        else:
            self.flow_block(generated_containing_block)

        # Only now set border_edge_height (now that generated containing block
        # height has been resolved).
        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                value = value * containing_block.height
            return value

        content_bottom = computed('border-bottom-width') + \
            used('padding-bottom')
        self.border_edge_height = self.content_top + \
            generated_containing_block.height + content_bottom

    def flow_block(self, containing_block):
        y = 0
        for child in self.children:
            child.flow(containing_block)
            y += child.margin_top + \
                child.border_edge_height + child.margin_bottom
        
        if containing_block.height is None:
            containing_block.height = y

        y = self.content_top
        for child in self.children:
            y += child.margin_top
            child.position(
                self.content_left + child.margin_left, 
                self.content_top + y, containing_block)
            y += child.border_edge_height + child.margin_bottom

    def flow_inline(self, containing_block):
        width = containing_block.width
        lines = [LineBox(self)]
        buffer = []
        children = self.children[:]
        y = 0
        while children:
            child = children.pop(0)
            child.flow_inline(containing_block, width)

            # The child goes straight into the line, it fits within width
            # and has a valid breakpoint.
            if child.fit_flow:
                for f in buffer:
                    f.flow_inline(containing_block, width)
                    lines[-1].add(f)
                buffer = []
                lines[-1].add(child)
                width -= child.margin_left + child.border_edge_width + \
                    child.margin_right

            # Continuation does not fit and/or doesn't have a valid breakpoint
            if child.continuation:
                buffer.append(child.continuation)
                width -= child.continuation.margin_left + \
                         child.continuation.border_edge_width + \
                         child.continuation.margin_right

            if width < 0 and not lines[-1].is_empty:
                # No more children will fit, close the line
                y += lines[-1].line_height
                lines.append(LineBox(self))
                width = containing_block.width
                children = buffer + children
                buffer = []
  
        # Final unfinished line
        for f in buffer:
            f.flow_inline(containing_block, width)
            lines[-1].add(f)
        if lines[-1].is_empty:
            del lines[-1]
        else:
            y += lines[-1].line_height

        if containing_block.height is None:
            containing_block.height = y

        y = self.content_top
        for line in lines:
            line.position(self.content_left, y, self.containing_block)
            y += line.line_height

class LineBox(object):
    '''Transient box for collecting lines of inline frames and aligning
    them vertically and horizontally.
    '''

    def __init__(self, parent):
        self.parent = parent
        self.line_ascent = 0
        self.line_descent = 0
        self.frames = []
        self.is_empty = True
        self.line_height = self.parent.get_computed_property('line-height')
        if self.line_height == 'normal':
            self.line_height = 0

    def add(self, frame):
        self.frames.append(frame)
        self.line_ascent = max(self.line_ascent, frame.line_ascent)
        self.line_descent = min(self.line_descent, frame.line_descent)
        self.line_height = max(self.line_height, 
                               self.line_ascent - self.line_descent)

    def position(self, x, y, containing_block):
        # Determine half-leading
        half_leading = (self.line_height - 
                        (self.line_ascent - self.line_descent)) / 2
        self.line_ascent += half_leading
        self.line_descent -= half_leading

        # Position frames in this line
        x = 0
        for frame in self.frames:
            x += frame.margin_left
            valign = frame.get_computed_property('vertical-align')
            if valign == 'baseline':
                y = self.line_ascent - frame.content_ascent + frame.margin_top
            elif valign == 'top':
                y = frame.margin_top
            else:
                raise NotImplementedError('Unsupported vertical-align')
            frame.position(x, y, containing_block)
            x += frame.border_edge_width + frame.margin_right

class InlineFrame(Frame):
    inline_level = True
    inline_context = True

    fit_flow = True

    def __init__(self, style, element):
        super(InlineFrame, self).__init__(style, element)
        self.flowed_children = ()

    def flow_inline(self, containing_block, width):
        self.continuation = None

        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                value = value * containing_block.width
            return value

        content_right = computed('border-right-width') + used('padding-right')
        content_bottom = computed('border-bottom-width') + used('padding-bottom')
        self.content_top = computed('border-top-width') + used('padding-top')
        self.margin_right = used('margin-right')
        if not self.is_continuation:
            self.margin_left = used('margin-left')
            self.content_left = computed('border-left-width') + used('padding-left') 

        line_ascent = 0
        line_descent = 0
        content_ascent = 0
        content_descent = 0

        width -= self.margin_left + content_left + \
            content_right + self.margin_right

        committed = []
        buffer = []
        for i, child in enumerate(self.children):
            child.flow(containing_block, width)
            if child.fit_flow:
                committed += buffer
                buffer = []
                committed.append(child)
                width -= child.margin_left + \
                    child.border_edge_width + child.margin_right

            if child.continuation:
                buffer.append(child.continuation)
                width -= child.continuation.margin_left + \
                         child.continuation.border_edge_width + \
                         child.continuation.margin_right

            if width < 0:
                buffer += self.children[i+1:]
                break

        if buffer:
            self.continuation = InlineFrame(self.style, self.element)
            self.continuation.children = buffer
            self.continuation.is_continuation = True
            self.margin_right = 0
            content_right = 0
        self.fit_flow = len(committed) > 0

        content_width = 0
        for child in committed:
            line_ascent = max(line_ascent, child.line_ascent)
            line_descent = min(line_descent, child.line_descent)
            content_ascent = max(content_ascent, child.content_ascent)
            content_descent = max(content_descent, child.content_descent)
            content_width += child.margin_left + child.border_edge_width + \
                child.margin_right

        line_height = self.get_computed_property('line-height')
        if line_height != 'normal':
            half_leading = (line_height - 
                            (content_ascent - content_descent)) / 2
            line_ascent += half_leading
            line_descent -= half_leading

        self.line_ascent = line_ascent
        self.line_descent = line_descent
        self.content_ascent = content_ascent
        self.content_descent = content_descent

        self.border_edge_width = self.content_left + \
            content_width + content_right
        self.border_edge_height = self.content_top + \
            (self.content_ascent - self.content_descent) + \
            content_bottom

        self.flowed_children = committed

    def position(self, x, y, containing_block):
        c = self.children
        self.children = self.flowed_children
        super(InlineFrame, self).position(x, y, containing_block)
        self.children = c

    def draw(self, x, y, render_device):
        c = self.children
        self.children = self.flowed_children
        super(InlineFrame, self).draw(x, y, render_device)
        self.children = c

class TextFrame(InlineFrame):
    def __init__(self, style, element, text):
        super(TextFrame, self).__init__(style, element)
        self.text = text

    def draw(self, x, y, render_device):
        orig_x, orig_y = x, y

        x += self.border_edge_left
        y -= self.border_edge_top

        self.draw_background(x, y, render_device)
        self.draw_border(x, y, render_device)

        self.draw_text(x, y - self.content_ascent, render_device)

        if self.continuation:
            self.continuation.draw(orig_x, orig_y, render_device)
        
    def draw_text(self, x, y, render_context):
        '''Draw text with baseline at y.'''
        raise NotImplementedError('abstract')

    # Debug methods
    # -------------    

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.text)

class FrameBuilder(object):
    '''Construct and update the frame tree for a content tree.
    '''

    display_element_classes = {
        'inline':   InlineFrame,
        'block':    BlockFrame
    }

    def __init__(self, document, render_device):
        self.document = document
        self.render_device = render_device
        self.style_tree = StyleTree(render_device)

        self.replaced_element_builders = {}

    def create_frame(self, element):
        if element.is_anonymous:
            declaration_sets = []
        else:
            declaration_sets = self.get_element_declaration_sets(element)
        style_node = self.style_tree.get_style_node(declaration_sets)

        temp_frame = Frame(style_node, element)
        display = style_node.get_computed_property('display', temp_frame) 
        if display == 'none':
            return

        if element.text and display == 'inline':
            return self.create_text_frame(style_node, element, element.text)

        if element.name in self.replaced_element_builders:
            builder = self.replaced_element_builders[element.name]
            frame = builder.build(style_node, element)
        elif display in self.display_element_classes:
            frame_class = self.display_element_classes[display]
            frame = frame_class(style_node, element)
        else:
            warnings.warn('Unsupported display type "%s"' % display)
            return None

        if element.text:
            text_frame = self.create_text_frame(
                self.style_tree.get_style_node([]),
                AnonymousElement(element),
                element.text)
            if text_frame:
                frame.children = [text_frame]

        return frame

    def get_element_declaration_sets(self, element):
        declaration_sets = []
        for stylesheet in self.document.stylesheets:
            declaration_sets += stylesheet.get_element_declaration_sets(element)
        if element.element_declaration_set:
            declaration_sets.append(element.element_declaration_set)
        return declaration_sets

    def build_frame(self, element):
        '''Recursively build a frame for element and all its children.

        Returns the frame, or None if no frames were generated (e.g.
        display = none).
        '''
        frame = self.create_frame(element)

        if not frame:
            return None

        if element.children:
            frame.children = []
        for element_child in element.children:
            child = self.build_frame(element_child)
            if not child: 
                continue

            # Anonymous box creation, see 9.2.1
            if child.inline_level and not frame.inline_context:
                # Don't create anonymous block box when white-space will
                # collapse it later anyway.
                if (not child.children and
                    not child.text.strip() and
                    child.get_computed_property('white-space') in
                        ('normal', 'nowrap', 'pre-line')):
                    continue
                elif frame.children[-1].element.is_anonymous:
                    # Piggy-back this inline into the previous anon frame
                    frame.children[-1].children.append(child)
                    child.parent = frame.children[-1]
                    continue
                else:
                    child = self.anonymous_block_frame([child], frame)
            elif (not child.inline_level and
                  not frame.inline_level and 
                  frame.inline_context):
                # Convert frame to block context
                frame.inline_context = False

                # Discard children if only collapsable white-space
                if (len(frame.children) == 0 or
                    (len(frame.children) == 1 and
                     not frame.children[0].text.strip() and
                     frame.children[0].get_computed_property('white-space') in
                        ('normal', 'nowrap', 'pre-line'))):
                    frame.children = []
                else:
                    # Otherwise wrap them in an anonymous block frame
                    frame.children = [
                        self.anonymous_block_frame(frame.children, frame)]

            child.parent = frame
            frame.children.append(child)

        return frame

    def anonymous_block_frame(self, children, parent):
        element = AnonymousElement(parent.element)
        style = self.style_tree.get_style_node([])
        frame = BlockFrame(style, element)
        frame.children = children
        for child in children:
            child.parent = frame
        return frame

    ws_normalize_pattern = re.compile('\r\n|\n|\r')
    ws_step1_pattern = re.compile('[ \r\t]*\n[ \r\t]*')
    ws_step2a_pattern = re.compile('( +)')
    ws_step2_pattern = re.compile(' ')
    ws_step3_pattern = re.compile('\n') 
    ws_step4a_pattern = re.compile('\t')
    ws_step4b_pattern = re.compile(' +')

    def create_text_frame(self, style, element, text):
        frame = self.render_device.create_text_frame(style, element, text)
        white_space = frame.get_computed_property('white-space')

        # Normalize newlines to \n.  This isn't part of CSS, but I think I saw
        # it somewhere in XML.  Anyway, it's needed.
        text = self.ws_normalize_pattern.sub('\n', text)

        # Collapse white-space according to 16.6.1.
        # Step 1
        if white_space in ('normal', 'nowrap', 'pre-line'):
            # Remove white-space surrounding a newline
            text = self.ws_step1_pattern.sub('\n', text)

        # Step 2
        if white_space in ('pre', 'pre-wrap'):
            if white_space == 'pre-wrap':
                # Break opportunity after sequence of spaces
                text = self.ws_step2a_pattern.sub(u'\\1\u200b', text)
            # Replace spaces with non-breaking spaces
            text = self.ws_step2_pattern.sub(u'\u00a0', text)

        # Step 3
        if white_space in ('normal', 'nowrap'):
            # Replace newlines with space (TODO in some scripts, use
            # zero-width space or no character)
            text = self.ws_step3_pattern.sub(' ', text) 

        # Step 4
        if white_space in ('normal', 'nowrap', 'pre-line'):
            # Replace tabs with spaces
            text = self.ws_step4a_pattern.sub(' ', text)
            # Collapse consecutive spaces
            text = self.ws_step4b_pattern.sub(' ', text)
            # Must also strip leading space if the previous inline ends
            # with a space.  Can't do this until reflow.

        if not text:
            return None

        frame.text = text
        return frame
