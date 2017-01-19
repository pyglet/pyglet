#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import warnings

from layout.content import *
from layout.properties import *

import re

__all__ = ['ContainingBlock', 'FrameBuilder', 'TextFrame',
           'ReplacedElementDrawable', 'ReplacedElementFactory']

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
    containing_block = None
    parent = None
    children = ()
    flowed_children = ()
    text = ''
    style = None
    computed_properties = None
    continuation = None
    is_replaced = False     # True if a replaced element

    open_border = True      # False for continued frames (usually)
    close_border = True     # False for continuation frames (usually)

    # Incremental reflow flag
    flow_dirty = True

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

    def purge_style_cache(self, properties):
        '''Clear the cache of the given set of property names.

        Only applies to local frame cache, not style node cache. 
        '''
        for property in properties:
            if property in self.computed_properties:
                del self.computed_properties[property]

        for child in self.children:
            child.purge_style_cache(properties)

    def mark_flow_dirty(self):
        '''Mark this frame and all its descendents for reflow, 
        '''
        self.flow_dirty = True
        for child in self.children:
            child.mark_flow_dirty()

    def get_layout_metrics(self):
        return (self.border_edge_width, self.border_edge_height,
                self.margin_top, self.margin_right, 
                self.margin_bottom, self.margin_left)

    # Reflow
    # ------

    def flow(self):
        '''Flow and position all children, size self.
        '''
        raise NotImplementedError('abstract')

    def get_flow_master(self):
        '''Return the frame responsible for flowing this one.  Typically
        'self'.
        '''
        return self

    def position(self, x, y):
        '''Position self border edge top-left at x, y.

        Children are affected by relativity only (no child-positioning code
        here).
        '''
        self.border_edge_left = x
        self.border_edge_top = y
        if self.get_computed_property('position') == 'relative':
            left = self.get_computed_property('left')
            top = self.get_computed_property('top')
            if type(left) == Percentage:
                left = left * self.containing_block.width
            elif left == 'auto':
                left = 0
            if type(top) == Percentage:
                top = top * self.containing_block.height
            elif top == 'auto':
                top = 0

            self.border_edge_left += left
            self.border_edge_top += top

    # Drawing and hit-testing
    # -----------------------

    # TODO: drawing/hit-testing is currently Y+up instead of against the
    # canvas Y+down.

    def draw_cull(self, x, y, render_device, left, top, right, bottom):
        '''Draw this frame if it is within the given bounding box.
        '''
        # Check for entirely outside
        if self.bounding_box_left >= right or \
           self.bounding_box_right <= left or \
           self.bounding_box_top <= bottom or \
           self.bounding_box_bottom >= top:
            return

        # Check for entirely inside
        if self.bounding_box_left >= left and \
           self.bounding_box_right <= right and \
           self.bounding_box_top <= top and \
           self.bounding_box_bottom >= bottom:
            self.draw_no_cull(x, y, render_device)
            return
        
        # Overlaps bounding box.
        lx = x + self.border_edge_left
        ly = y - self.border_edge_top

        self.draw_background(lx, ly, render_device)
        self.draw_border(lx, ly, render_device)

        for child in self.flowed_children:
            child.draw_cull(lx, ly, render_device, left, top, right, bottom)
        
    def draw_no_cull(self, x, y, render_device):
        '''Draw this frame with border_edge relative to given x,y.
        '''
        lx = x + self.border_edge_left
        ly = y - self.border_edge_top

        self.draw_background(lx, ly, render_device)
        self.draw_border(lx, ly, render_device)

        for child in self.flowed_children:
            child.draw_no_cull(lx, ly, render_device)

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

        if not self.open_border:
            bleft = 0
        if not self.close_border:
            bright = 0

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

        for child in self.flowed_children:
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
            for child in self.flowed_children:
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

    def pprint_flowed(self, indent=''):
        import textwrap
        print '\n'.join(textwrap.wrap(repr(self), 
            initial_indent=indent, subsequent_indent=indent))
        for child in self.flowed_children:
            child.pprint_flowed(indent + '  ')

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

class InlineFormattingContext(object):
    def __init__(self, containing_block):
        # Width remaining on current line
        self.remaining_width = containing_block.width
        # Width of next line (make dynamic with float)
        self.next_line_width = containing_block.width
        # Also allow this much space (e.g. for end of frame)
        self.reserved_width = 0
        # Width already expended on next line
        self.next_line_carry = 0
        # True if current frame has no content
        self.line_empty = True
        # True if white-space from beginning of next frame needs collapsing
        self.strip_next = False

    def reserve(self, width):
        self.reserved_width += width

    def can_add(self, width, ignore_reserve=False):
        if ignore_reserve:
            return width <= self.remaining_width and not self.line_empty
        else:
            return width + self.reserved_width <= self.remaining_width and \
                   not self.line_empty

    def add(self, width):
        self.remaining_width -= width
        self.next_line_carry += width
        self.line_empty = False

    def breakpoint(self):
        self.next_line_carry = 0

    def newline(self):
        self.remaining_width = self.next_line_width - self.next_line_carry
        self.line_empty = self.next_line_carry > 0
        self.next_line_carry = 0

    def copy(self):
        c = object.__new__(InlineFormattingContext)
        c.remaining_width = self.remaining_width
        c.next_line_width = self.next_line_width
        c.next_line_carry = self.next_line_carry
        c.reserved_width = self.reserved_width
        c.line_empty = self.line_empty
        #c.line_empty = True  # not inherited
        c.strip_next = self.strip_next
        return c

class BlockFrame(Frame):
    inline_level = False
    inline_context = True       # Flips if a block-level child is added

    def create_containing_block(self):
        '''Also sets frame metrics with the exception of 
        border_edge_height, if implicit.

        Returns generated containing block.
        '''
        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                value = value * self.containing_block.width
            return value
        
        # Calculate computed and used values of box properties when
        # relative to containing block width.
        content_right = computed('border-right-width') + used('padding-right')
        self.content_left = computed('border-left-width') + used('padding-left')
        self.content_top = computed('border-top-width') + used('padding-top')
        self.content_bottom = computed('border-bottom-width') + \
            used('padding-bottom')
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
        remaining_width = self.containing_block.width - non_content_width

        # Determine content width
        content_width = computed('width')
        if content_width == 'auto':
            content_width = self.containing_block.width - non_content_width
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
            if self.containing_block.bottom is None:
                content_height = 'auto'
            else:
                content_height =  content_height * self.containing_block.height

        if content_height == 'auto':
            return ContainingBlock(content_width, None)
        else:
            return ContainingBlock(content_width, content_height)


    def flow(self):
        '''Flow all children, size self.
        '''
        child_containing_block = self.create_containing_block()
        if self.inline_context:
            self.flow_for_inline_context(child_containing_block)
        else:
            self.flow_for_block_context(child_containing_block)

        self.border_edge_height = self.content_top + \
            child_containing_block.height + self.content_bottom
        self.flow_dirty = False

    class BlockPositionIterator(object):
        '''Encapsulate block positioning logic, used by flow size calculation
        and child positioning.  Accounts for vertical margin collapse.

        Instantiate with parent frame, then for each child that will be 
        placed, call next(child) to get that child's y position.  After
        iteration ends, 'y' gives the height of the content, and
        'margin_collapse' gives the amount of margin on the final frame.
        '''
        def __init__(self, parent_frame):
            self.y = 0
            self.margin_collapse = 0
            if not parent_frame.content_top:
                self.margin_collapse = parent_frame.margin_top

        def next(self, child_frame):
            self.y += max(child_frame.margin_top - self.margin_collapse, 0)
            result = self.y
            self.y += child_frame.border_edge_height + child_frame.margin_bottom
            self.margin_collapse = child_frame.margin_bottom
            return result

    def flow_for_block_context(self, child_containing_block):
        it = self.BlockPositionIterator(self)
        self.flowed_children = self.children
        for child in self.children:
            child.containing_block = child_containing_block
            if child.flow_dirty:
                child.flow()
            it.next(child)

        if child_containing_block.height is None:
            child_containing_block.height = it.y

        if not self.content_bottom:
            self.margin_bottom = max(self.margin_bottom, it.margin_collapse, 0)

        it = self.BlockPositionIterator(self)
        for child in self.flowed_children:
            y = it.next(child)
            child.position(self.content_left + child.margin_left, 
                           self.content_top + y)

    def flow_for_inline_context(self, child_containing_block):
        strip_lines = self.get_computed_property('white-space') in \
            ('normal', 'nowrap', 'pre-line')
        lines = [LineBox(self, strip_lines)]
        buffer = []
        y = 0
        self.flowed_children = []

        context = InlineFormattingContext(child_containing_block)

        for child in self.children:
            child.containing_block = child_containing_block
            if child.flow_dirty:
                child.flow_inline(context)

            while child:
                # Avoid adding empty frames into line box
                if strip_lines and lines[-1].is_empty:
                    child.lstrip()
                if not child.border_edge_width:
                    child = child.continuation
                    continue

                self.flowed_children.append(child)
                context.strip_next = child.strip_next
                child_width = child.margin_left + child.border_edge_width + \
                    child.margin_right
                if not context.can_add(child_width):
                    # This child will not fit, start a new line
                    context.newline()
                    y += lines[-1].line_height
                    lines.append(LineBox(self, strip_lines))

                context.add(child_width)
                buffer.append(child)

                if child.soft_break:
                    for f in buffer:
                        lines[-1].add(f)
                    buffer = []
                    context.breakpoint()

                if child.line_break:
                    # Start new line after the child
                    for f in buffer:
                        lines[-1].add(f)
                    y += lines[-1].line_height
                    lines.append(LineBox(self, strip_lines))
                    buffer = []
                    context.newline()

                child = child.continuation
  
        # Final unfinished line
        for f in buffer:
            lines[-1].add(f)
        if lines[-1].is_empty:
            del lines[-1]
        else:
            y += lines[-1].line_height

        if child_containing_block.height is None:
            child_containing_block.height = y

        y = self.content_top
        for line in lines:
            line.position(self.content_left, y, child_containing_block)
            y += line.line_height

class LineBox(object):
    '''Transient box for collecting lines of inline frames and aligning
    them vertically and horizontally.
    '''

    def __init__(self, parent, strip_lines):
        self.parent = parent
        self.strip_lines = strip_lines
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
        self.is_empty = False

    def position(self, x, y, containing_block):
        # Determine half-leading
        half_leading = (self.line_height - 
                        (self.line_ascent - self.line_descent)) / 2
        self.line_ascent += half_leading
        self.line_descent -= half_leading

        baseline = y + self.line_ascent

        # Position frames in this line
        for frame in self.frames:
            x += frame.margin_left
            valign = frame.get_computed_property('vertical-align')
            if valign == 'baseline':
                ly = baseline - frame.baseline + frame.margin_top
            elif valign == 'top':
                ly = y + frame.margin_top
            else:
                raise NotImplementedError('Unsupported vertical-align')
            frame.position(x, ly)
            x += frame.border_edge_width + frame.margin_right


class InlineFrame(Frame):
    inline_level = True
    inline_context = True

    soft_break = False  # if True, break opportunity after this frame
    line_break = False  # if True, line break after this frame
    strip_next = False  # if True, strip leading space from next frame

    line_ascent = 0
    line_descent = 0
    content_ascent = 0
    content_descent = 0
    baseline = 0        # +ve distance from top of border to baseline

    def __init__(self, style, element):
        super(InlineFrame, self).__init__(style, element)
        self.flowed_children = ()

    def get_flow_master(self):
        # Can't flow self, rely on ancestor non-inline frame to call this
        # frame's flow_inline method.
        if self.parent:
            # Force reflow (this might not be set if it's a descendent with
            # the 'real' dirty bit).
            self.frame_dirty = True 
            return self.parent.get_flow_master()

        # Hopeless case: inline as root element.
        return self

    def lstrip(self):
        if self.flowed_children:
            self.flowed_children[0].lstrip()

    def flow_inline(self, context):
        context = context.copy()
        self.continuation = None
        self.close_border = True

        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                value = value * self.containing_block.width
            elif value == 'auto':
                # actually only for margin-left, margin-right, top, left,
                # but no harm done
                value = 0   
            return value

        content_right = computed('border-right-width') + used('padding-right')
        content_bottom = computed('border-bottom-width') + \
            used('padding-bottom')
        self.content_top = computed('border-top-width') + used('padding-top')
        self.margin_right = used('margin-right')
        self.margin_left = used('margin-left')
        self.content_left = computed('border-left-width') + used('padding-left') 
        line_height = computed('line-height')

        context.add(self.margin_left + self.content_left)
        self.border_edge_width = self.content_left

        def add(child):
            # Correct vertical height for child that was split but turns out
            # to be in the same line.
            if frame.flowed_children and \
               child == frame.flowed_children[-1].continuation and False:
                prev = frame.flowed_children[-1]
                child.line_ascent = max(child.line_ascent, 
                                        prev.line_ascent)
                child.content_ascent = max(child.content_ascent, 
                                           prev.content_ascent)
                child.line_descent = min(child.line_descent, 
                                         prev.line_descent)
                child.content_descent = min(child.content_descent, 
                                            prev.content_descent)
                child.border_edge_height = self.content_top + content_bottom + \
                    child.line_ascent - child.line_descent

            frame.flowed_children.append(child)
            frame.border_edge_width += child.margin_left + \
                child.border_edge_width + child.margin_right
            frame.line_ascent = max(frame.line_ascent, child.line_ascent)
            frame.line_descent = min(frame.line_descent, child.line_descent)
            frame.content_ascent = max(frame.content_ascent, 
                                       child.content_ascent)
            frame.content_descent = min(frame.content_descent, 
                                        child.content_descent)
            frame.soft_break = child.soft_break

        def init(frame):
            frame.line_ascent = 0
            frame.line_descent = 0
            frame.content_ascent = 0
            frame.content_descent = 0
            frame.flowed_children = []

        def finish(frame):
            frame.border_edge_height = self.content_top + content_bottom + \
                frame.line_ascent - frame.line_descent
            frame.baseline = self.content_top + frame.content_ascent
            #if line_height == 'normal':
            #    frame.line_ascent = frame.content_ascent
            #    frame.line_descent = frame.content_descent

        frame = self
        init(frame)
        buffer = []
        ignore_reserve = True
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                context.reserve(self.margin_right + content_right)

            if child.flow_dirty:
                child.containing_block = self.containing_block
                child.flow_inline(context)

            while child:
                if i == len(self.children) - 1 and not child.continuation:
                    ignore_reserve = False

                context.strip_next = child.strip_next
                c_width = child.margin_left + child.border_edge_width + \
                    child.margin_right

                if not context.can_add(c_width, ignore_reserve):
                    if not frame.flowed_children:
                        context.newline()
                    else:
                        continuation = InlineFrame(self.style, self.element)
                        continuation.open_border = False
                        continuation.margin_right = self.margin_right
                        init(continuation)

                        finish(frame)
                        context.newline()
                         
                        frame.margin_right = 0

                        frame.continuation = continuation
                        frame.close_border = False
                        frame = continuation

                context.add(c_width)
                buffer.append(child)

                if child.soft_break:
                    for f in buffer:
                        add(f)
                    buffer = []
                    context.breakpoint()

                child = child.continuation

        if buffer:
            continuation = InlineFrame(self.style, self.element)
            continuation.open_border = False
            continuation.margin_right = self.margin_right
            init(continuation)

            finish(frame)
            frame.margin_right = 0
            frame.continuation = continuation
            frame.close_border = False
            frame = continuation
            for f in buffer:
                add(f)
        finish(frame)

        frame.border_edge_width += content_right
        self.flow_dirty = False
        
    def position(self, x, y):
        super(InlineFrame, self).position(x, y)
        x = self.content_left
        baseline = self.baseline
        for child in self.flowed_children:
            x += child.margin_left
            valign = child.get_computed_property('vertical-align')
            if valign == 'baseline':
                ly = baseline - child.baseline + child.margin_top
            elif valign == 'top':
                ly = child.margin_top
            child.position(x, ly)
            x += child.border_edge_width + child.margin_right

class TextFrame(InlineFrame):
    def __init__(self, style, element, text):
        super(TextFrame, self).__init__(style, element)
        self.text = text

    def draw_cull(self, x, y, render_device, left, top, right, bottom):
        self.draw_no_cull(x, y, render_device) # TODO
        
    def draw_no_cull(self, x, y, render_device):
        x += self.border_edge_left
        y -= self.border_edge_top

        self.draw_background(x, y, render_device)
        self.draw_border(x, y, render_device)

        # Align baseline to integer (not background/border, that screws up
        # touching borders).
        rounding = (y - self.baseline) - int(y - self.baseline)
        y -= rounding

        self.draw_text(x + self.content_left, 
                       y - self.baseline, 
                       render_device)

    def draw_text(self, x, y, render_context):
        '''Draw text with baseline at y.'''
        raise NotImplementedError('abstract')

    # Debug methods
    # -------------    

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.text)

class ReplacedElementDrawable(object):
    intrinsic_width = None
    intrinsic_height = None
    intrinsic_ratio = None

    def draw(self, frame, render_device, left, top, right, bottom):
        raise NotImplementedError('abstract')

class InlineReplacedElementFrame(InlineFrame):
    is_replaced = True

    def __init__(self, style, element, drawable):
        super(InlineReplacedElementFrame, self).__init__(style, element)
        # Always allow a line break before a replaced element.  Make this
        # frame empty and put everything in the continuation.
        self.margin_left = 0
        self.border_edge_width = 0
        self.margin_right = 0
        self.content_ascent = self.content_descent = 0
        self.line_ascent = self.line_descent =  0
        self.border_edge_height = 0
        self.close_border = False
        self.open_border = False

        self.continuation = InlineReplacedElementDelegate(self, drawable)

    def purge_style_cache(self, properties):
        super(InlineReplacedElementFrame, self).purge_style_cache(properties)
        self.continuation.purge_style_cache(properties)

    def mark_flow_dirty(self):
        super(InlineReplacedElementFrame, self).mark_flow_dirty()
        self.continuation.mark_flow_dirty()

    def flow_inline(self, context):
        # Let continuation flow itself.
        self.continuation.containing_block = self.containing_block
        self.continuation.style = self.style
        self.continuation.flow_inline(context)

    def draw(self, x, y, render_device):
        pass  # continuation only is drawn.

class InlineReplacedElementDelegate(InlineFrame):
    is_replaced = True

    def __init__(self, continued_frame, drawable):
        super(InlineReplacedElementDelegate, self).__init__(
            continued_frame.style, continued_frame.element)
        self.drawable = drawable
        self.continued_frame = continued_frame

        # Add an empty continuation to allow for line-breaks after this
        # frame.
        self.continuation = InlineFrame(self.style, self.element)
        self.continuation.open_border = False
        self.continuation.close_border = False

    def flow_inline(self, context):
        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                return value * self.containing_block.width
            elif value == 'auto':
                return 0
            return value

        self.margin_left = used('margin-left')
        self.margin_right = used('margin-right')
        self.margin_top = used('margin-top')
        self.margin_bottom = used('margin-bottom')
        self.content_top = computed('border-top-width') + used('padding-top')
        self.content_left = computed('border-left-width') + used('padding-left')
        content_right = computed('border-right-width') + used('padding-right')
        content_bottom = computed('border-bottom-width') + \
            used('padding-bottom')

        # See 10.3.2

        intrinsic_width = self.drawable.intrinsic_width
        intrinsic_height = self.drawable.intrinsic_height
        intrinsic_ratio = self.drawable.intrinsic_ratio
        
        content_width = computed('width')
        if type(content_width) == Percentage:
            if self.containing_block.width is not None:
                content_width = content_width * self.containing_block.width
            else:
                content_width = 'auto'
        computed_width = content_width # save for height calc later

        content_height = computed('height')
        if type(content_height) == Percentage:
            if self.containing_block.height is not None:
                content_height = content_height * self.containing_block.height
            else:
                content_height = 'auto'

        if content_width == 'auto':
            if content_height == 'auto':
                if intrinsic_width is not None:
                    content_width = intrinsic_width
                elif (intrinsic_height is not None and
                      intrinsic_ratio is not None):
                    content_width = intrinsic_height * intrinsic_ratio
            elif intrinsic_ratio is not None:
                content_width = content_height * intrinsic_ratio
        if content_width == 'auto':
            content_width = self.style.render_device.dimension_to_device(
                Dimension('300px'))

        # See 10.6.2
        # For these calculations use computed_width, which may be 'auto'
        # even though content_width has already been worked out.

        if content_height == 'auto':
            if computed_width == 'auto':
                if intrinsic_height is not None:
                    content_height = intrinsic_height
                elif (intrinsic_width is not None and
                      intrinsic_ratio is not None):
                    content_height = content_width / intrinsic_ratio
            elif intrinsic_ratio is not None:
                content_height = content_width / intrinsic_ratio
        if content_height == 'auto':
            content_height = self.style.render_device.dimension_to_device(
                Dimension('150px'))

        # Use for drawing
        self.content_width = content_width
        self.content_height = content_height

        self.border_edge_width = \
            self.content_left + \
            self.content_width + \
            content_right
        self.border_edge_height = \
            self.content_top + \
            self.content_height + \
            content_bottom
        
        # XXX This is wrong for most vertical-aligns.
        self.content_ascent = self.line_ascent = \
            self.border_edge_height + self.margin_top + self.margin_bottom
        self.content_descent = self.line_descent = 0
        self.baseline = self.content_ascent

    def draw_cull(self, x, y, render_device, left, top, right, bottom):
        # Check for partial intersection
        if self.bounding_box_right > left and \
           self.bounding_box_left < right and \
           self.bounding_box_top > bottom and \
           self.bounding_box_bottom < top:
            self.draw_no_cull(x, y, render_device)

    def draw_no_cull(self, x, y, render_device):
        lx = x + self.border_edge_left
        ly = y - self.border_edge_top

        self.draw_background(lx, ly, render_device)
        self.draw_border(lx, ly, render_device)

        self.drawable.draw(self.continued_frame, render_device,
            lx + self.content_left, 
            ly - self.content_top, 
            lx + self.content_left + self.content_width, 
            ly - self.content_top - self.content_height)
            
class ReplacedElementFactory(object):
    accept_names = None

    def create_drawable(self, element):
        '''Simple use: override just this method to return an implementation
        of ReplacedElementDrawable.

        Return None if no frame should be created.
        '''
        raise NotImplementedError('abstract')

    def create_frame(self, display, style, element):
        '''Called by FrameBuilder to construct the frame.  Default
        implementation calls 'create_drawable' and creates the appropriate
        frame depending on display property.

        Default implementation also inspects element attributes for 
        'width' and 'height' attributes and uses these for intrinsic
        width and height if specified.

        Return None if no frame should be created.
        '''
        drawable = self.create_drawable(element)
        if drawable is None:
            return None

        if display == 'inline':
            frame = InlineReplacedElementFrame(style, element, drawable)
        else:
            warnings.warn(('Display type "%s" unsupported for ' + 
                'replaced elements.') % display)
            return None

        if 'width' in element.attributes:
            frame.intrinsic_width = element.attributes['width']
        if 'height' in element.attributes:
            frame.intrinsic_height = element.attributes['height']

        return frame

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

        self.replaced_element_factories = {}

    def add_replaced_element_factory(self, factory):
        if not factory.accept_names:
            raise RuntimeError('No accept_names specified on factory.')
        for name in factory.accept_names:
            self.replaced_element_factories[name] = factory

    def get_style_node(self, element):
        if element.is_anonymous:
            declaration_sets = []
        else:
            declaration_sets = self.get_element_declaration_sets(element)
        return self.style_tree.get_style_node(declaration_sets)

    def create_frame(self, element, parent):
        style_node = self.get_style_node(element) 

        temp_frame = Frame(style_node, element)
        display = style_node.get_computed_property('display', temp_frame) 
        if display == 'none':
            element.frame = None
            return

        if element.text and display == 'inline':
            frame = self.create_text_frame(
                style_node, element, element.text, parent)
            element.frame = frame
            return frame

        if element.name in self.replaced_element_factories:
            factory = self.replaced_element_factories[element.name]
            frame = factory.create_frame(display, style_node, element)
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
                element.text,
                frame)
            if text_frame:
                frame.children = [text_frame]

        frame.parent = parent
        element.frame = frame
        return frame

    def get_element_declaration_sets(self, element):
        declaration_sets = []
        for stylesheet in self.document.stylesheets:
            declaration_sets += stylesheet.get_element_declaration_sets(element)
        if element.intrinsic_declaration_set:
            declaration_sets.append(element.intrinsic_declaration_set)
        if element.element_declaration_set:
            declaration_sets.append(element.element_declaration_set)
        return declaration_sets

    def build_frame(self, element, parent=None):
        '''Recursively build a frame for element and all its children.

        Returns the frame, or None if no frames were generated (e.g.
        display = none).
        '''
        frame = self.create_frame(element, parent)

        if not frame:
            return None

        if element.children:
            frame.children = []
        for element_child in element.children:
            child = self.build_frame(element_child, frame)
            if not child: 
                continue

            # Anonymous box creation, see 9.2.1
            if child.inline_level and not frame.inline_context:
                # Don't create anonymous block box when white-space will
                # collapse it later anyway.
                if (not child.children and
                    not child.text.strip() and
                    not child.is_replaced and 
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

    def create_text_frame(self, style, element, text, parent):
        frame = self.render_device.create_text_frame(style, element, text)
        frame.parent = parent
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
