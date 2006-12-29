#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.layout.base import *

# Interfaces
# ----------------------------------------------------------------------------

class RenderDevice(object):
    width = 0
    height = 0
    dpi = 96            # device units per in
    ppd = 1             # px per device unit
    ppi = ppd * dpi     # calculated px per in

    font_sizes = {
        'xx-small': Dimension('6pt'),
        'x-small':  Dimension('8pt'),
        'small': Dimension('10pt'),
        'medium': Dimension('12pt'),
        'large': Dimension('14pt'),
        'x-large': Dimension('16pt'),
        'xx-large': Dimension('24pt')
    }

    def get_named_font_size(self, name):
        return self.font_sizes[name]

    def dimension_to_pt(self, dimension):
        if dimension.unit == 'pt':
            return dimension
        elif dimension.unit == 'pc':
            return Dimension('%fpt' % (dimension / 12.))
        elif dimension.unit == 'in':
            return Dimension('%fpt' % (dimension * 72.))
        elif dimension.unit == 'cm':
            return Dimension('%fpt' % (dimension / 2.54 * 72.))
        elif dimension.unit == 'mm':
            return Dimension('%fpt' % (dimension / 10. / 2.54 * 72.))
        elif dimension.unit == 'px':
            return Dimension('%fpt' % (dimension / self.ppi * 72.))
        else:
            raise NotImplementedError

    def dimension_to_device(self, dimension, font_size):
        assert font_size.unit == 'pt'
        if dimension.unit == 'px':
            return dimension / self.ppd
        elif dimension.unit == 'in':
            return dimension * self.dpi
        elif dimension.unit == 'pt':
            return dimension / 72. * self.dpi
        elif dimension.unit == 'pc':
            return dimension / 12. / 72. * self.dpi
        elif dimension.unit == 'em':
            return dimension * font_size / 72. * self.dpi
        elif dimension.unit == 'ex':
            return dimension * font_size / 2 / 72. * self.dpi # guess only
        elif dimension.unit == 'cm':
            return dimension / 2.54 * self.dpi
        elif dimension.unit == 'mm':
            return dimension / 10. / 2.54 * self.dpi
        else:
            raise NotImplementedError

    def draw_vertical_border(self, x1, y1, x2, y2, color, style):
        pass

    def draw_horizontal_border(self, x1, y1, x2, y2, color, style):
        pass

    def draw_background(self, x1, y1, x2, y2, box):
        pass

    def set_clip(self, left, top, right, bottom):
        pass

    def get_font(self, box):
        raise NotImplementedError()

    def create_inline_text_boxes(self, font, text):
        raise NotImplementedError()



# Visual formatting model
# ----------------------------------------------------------------------------

class ContainingBlock(object):
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.content_bottom = top

    def get_width(self):
        return self.right - self.left
    width = property(get_width)

    def get_height(self):
        return self.bottom - self.top
    height = property(get_height)

    def get_content_height(self):
        return self.content_bottom - self.top
    content_height = property(get_content_height)

    def __repr__(self):
        return '%s(%d,%d -- %d,%d)' % (self.__class__.__name__,
            self.left, self.top, self.right, self.bottom)

class Frame(object):
    box = None
    children = None
    parent = None
    continuation = None

    # These relate to left/right borders.  (No paging yet).
    border_open = True
    border_close = True


    # Box model properties (see diagram in 8.1)
    # ------------------------------------------------------------------------

    # Border edge, relative to parent frame
    border_left = 0
    border_top = 0
    border_right = 0
    border_bottom = 0

    # Size of margin edge
    outer_width = 0   # LM + LB + LP + width + RP + RB + RM
    outer_height = 0  # TM + TB + TP + height + BP + BB + BM

    # Size of content edge
    content_width = 0
    content_height = 0

    def __init__(self, box, parent, containing_block):
        self.box = box
        self.parent = parent
        self.children = []
        self.containing_block = containing_block
        if box:
            self.calculate_used_sizes(containing_block)

    _percentage_containing_block_width_attributes = [
        'margin_top', 'margin_right', 'margin_bottom', 'margin_left',
        'padding_top', 'padding_right', 'padding_bottom', 'padding_left',
        'width', 'min_width', 'max_width'
    ]
    def calculate_used_sizes(self, containing_block):
        # XXX why aren't used values set on the frame instead of box?
        w = containing_block.width
        for attr in self._percentage_containing_block_width_attributes:
            value = getattr(self.box, attr)
            if isinstance(value, Percentage):
                value = value * w
            setattr(self.box, 'used_%s' % attr, value)

        if isinstance(self.box.height, Percentage):
            if containing_block.height:
                self.box.used_height = self.box.height * \
                                       containing_block.height
            else: 
                self.box.used_height = Ident('auto')
        else:
            self.box.used_height = self.box.height

        # TODO: special constriant resolution for min/max width and height
        # when width and height are both auto (that's a pretty unlikely
        # scenario, IMO).

        width = self.box.used_width
        height = self.box.used_height

        width = self.used_width(width, height)
        if self.box.max_width != 'none' and width > self.box.max_width:
            width = self.used_width(self.box.max_width, height)
        if width < self.box.min_width:
            width = self.used_width(self.box.min_width, height)

        height = self.used_height(width, height)
        if self.box.max_height != 'none' and height > self.box.max_height:
            height = self.used_height(width, self.box.max_height)
        if height < self.box.min_height:
            height = self.used_height(width, self.box.min_height)

        self.box.used_width = width
        self.box.used_height = height

    def used_width(self, width, height):
        # 10.3.2 Calculating widths and margins for inline replaced elements
        if self.box.display == 'inline' and not self.box.is_text:
            if width == 'auto':
                if height == 'auto':
                    if self.box.intrinsic_width is not None:
                        width = self.box.intrinsic_width
                    elif self.box.intrinsic_height is not None and \
                         self.box.intrinsic_ratio is not None:
                        width = self.box.intrinsic_height * \
                                self.box.intrinsic_ratio
                    else:
                        # XXX: error: should be 300px
                        width = 300
                elif self.box.intrinsic_ratio is not None: 
                    width = height * self.box.intrinsic_ratio
                else:
                    # XXX: error: should be 300px
                    width = 300
        return width

    def used_height(self, width, height):
        # 10.6.2 Height for inline replaced elements
        if self.box.display == 'inline' and not self.box.is_text:
            if height == 'auto':
                if self.box.intrinsic_ratio is not None:
                    height = width / self.box.intrinsic_ratio
                else:
                    # XXX: error: should be 150px
                    height = min(width / 2, 150)
        return height


    def add(self, frame):
        self.children.append(frame)

    def draw_border_and_background(self, render_device, x1, y1, x2, y2):
        if self.box:
            if self.box.background_color != 'transparent':
                render_device.draw_background(x1, y1, x2, y2, self.box)

            if self.box.border_top_width:
                render_device.draw_horizontal_border(
                    x1, y1, x2, y1 - self.box.border_top_width,
                    self.box.border_top_color, self.box.border_top_style)
            if self.box.border_right_width and self.border_close:
                render_device.draw_vertical_border(
                    x2, y1, x2 - self.box.border_right_width, y2,
                    self.box.border_right_color, self.box.border_right_style)
            if self.box.border_bottom_width:
                render_device.draw_horizontal_border(
                    x1, y2 + self.box.border_bottom_width, x2, y2,
                    self.box.border_bottom_color, self.box.border_bottom_style)
            if self.box.border_left_width and self.border_open:
                render_device.draw_vertical_border(
                    x1, y1, x1 + self.box.border_left_width, y2,
                    self.box.border_left_color, self.box.border_left_style)

    def draw(self, render_device, x, y):
        x1 = x + self.border_left
        y1 = y - self.border_top
        x2 = x + self.border_right
        y2 = y - self.border_bottom

        self.draw_border_and_background(render_device, x1, y1, x2, y2)
        for child in self.children:
            child.draw(render_device, x1, y1)

    def add(self, frame):
        assert frame not in self.children
        self.children.append(frame)

    def insert_after(self, reference, frame): 
        for child in self.children:
            child.draw(render_device, lx, ly)

    def add(self, frame):
        assert frame not in self.children
        self.children.append(frame)

    def insert_after(self, reference, frame):
        assert reference in self.children
        assert frame not in self.children
        index = self.children.index(reference)
        self.children.insert(index + 1, frame)

    def create_continuation(self):
        assert not self.continuation
        self.continuation = self.__class__()

    def split(self, break_frame=None):
        if break_frame:
            index = self.children.index(break_frame)
        else:
            index = len(self.children)

        self.create_continuation()
        self.continuation.children = self.children[index:]
        for child in self.continuation.children:
            child.parent = self.continuation
        self.children = self.children[:index]

        if self.parent:
            self.parent.insert_after(self, self.continuation)
            self.parent.split(self.continuation)

    def set_border_left(self, border_left):
        self.border_left = border_left
        self.border_right = border_left + self.content_width
        if self.border_open:
            self.border_right += self.box.border_left_width + \
                self.box.used_padding_left
        if self.border_close:
            self.border_right += self.box.used_padding_right + \
                self.box.border_right_width

    def set_border_top(self, border_top):
        self.border_top = border_top
        self.border_bottom = (
            border_top +
            self.box.border_top_width +
            self.box.used_padding_top +
            self.content_height +
            self.box.used_padding_bottom +
            self.box.border_bottom_width)

    def __repr__(self):
        return '%s(children=%r)' % (self.__class__.__name__, self.children)

    def pprint(self, indent=''):
        print '%s%s()' % (indent, self.__class__.__name__)
        for child in self.children:
            child.pprint(indent + '  ')

class ViewportFrame(Frame):
    def __init__(self):
        self.children = []
        self.parent = None

class BlockFrame(Frame):
    def __init__(self, box, parent, containing_block):
        super(BlockFrame, self).__init__(box, parent, containing_block)
        self.border_left = containing_block.left + box.used_margin_left
        self.border_right = containing_block.right - box.used_margin_right
        self.generated_containing_block = ContainingBlock(
            box.border_left_width + box.used_padding_left,
            box.border_top_width + box.used_padding_top,
            (self.containing_block.width - box.used_margin_left -
            box.used_margin_right
            - box.border_right_width - box.used_padding_right) ,
            0) # bottom ignored

    def close(self):
        self.border_bottom = self.border_top + \
            self.box.border_top_width + \
            self.box.used_padding_top + \
            self.generated_containing_block.content_height + \
            self.box.used_padding_bottom + \
            self.box.border_bottom_width

    def pprint(self, indent=''):
        print '%s%s(' % (indent, self.__class__.__name__)
        print '%sborder_left=%r, ' % (indent, self.border_left)
        print '%sborder_right=%r, ' % (indent, self.border_left)
        print '%sgenerated=%r, ' % (indent, self.generated_containing_block)
        print '%scontaining_block=%r)' % (indent, self.containing_block)
        for child in self.children:
            child.pprint(indent + '  ')

class InlineFrame(Frame):
    # Distance from this frame's baseline to top margin edge (+ve)
    ascent = 0
    # Distance from this frame's baseline to bottom margin edge (-ve)
    descent = 0

    # Space required for parent's left and right border, padding and margin,
    # required for inline layout.
    left_parent_bearing = 0
    right_parent_bearing = 0

    def create_continuation(self):
        assert not self.continuation
        self.continuation = InlineFrame(self.box, self.parent,
            self.containing_block)
        self.border_close = False
        self.continuation.border_open = False

    def close(self):
        # Calculate positions of children wrt. this frame's border edge.
        lsb = 0
        if self.border_open:
            lsb = self.box.used_padding_left + self.box.border_left_width 

        x = 0
        content_ascent = 0
        content_descent = 0
        inline_ascent = inline_descent = 0
        for frame in self.children:
            frame.close()
            lx = lsb + x
            if frame.border_open:
                lx += frame.box.used_margin_left
            frame.set_border_left(lx)
            x += frame.outer_width

            content_ascent = max(content_ascent, frame.content_ascent)
            content_descent = min(content_descent, frame.content_descent)
            inline_ascent = max(inline_ascent, frame.inline_ascent)
            inline_descent = min(inline_descent, frame.inline_descent)
        self.content_width = x
        self.calculate_outer_width()

        content_ascent += self.box.used_padding_top + self.box.border_top_width
        content_descent -= self.box.used_padding_bottom + \
                           self.box.border_bottom_width
        
        self.set_ascent_descent(content_ascent, content_descent, 
                                inline_ascent, inline_descent)

    def set_ascent_descent(self, content_ascent, content_descent, 
                           inline_ascent, inline_descent):
        # content_ascent and content_descent refer to content-area
        # inline_ascent and inline_descent refer to inline box (leading
        # applied)
        # See http://meyerweb.com/eric/css/inline-format.html for good
        # explanation. 
        self.content_ascent = content_ascent
        self.content_descent = content_descent
        self.content_height = content_ascent - content_descent

        if self.box.vertical_align in ('baseline', 'bottom', 'text-bottom'):
            self.inline_ascent = inline_ascent
            self.inline_descent = inline_descent
        elif self.box.vertical_align in ('top', 'text-top'):
            self.inline_ascent = inline_ascent - inline_descent
            self.inline_descent = 0
        elif self.box.vertical_align == 'middle':
            parent_middle = self.parent.box.font_size / 2.
            height = inline_ascent - inline_descent
            self.inline_ascent = parent_middle + height / 2
            self.inline_descent = parent_middle - height / 2

    def vertical_align(self, line_box_top, parent_baseline, line_box_bottom):
        if self.box.vertical_align == 'baseline':
            self.set_border_top(parent_baseline - self.content_ascent)
        elif self.box.vertical_align == 'top':
            self.set_border_top(line_box_top)
        else:
            raise NotImplementedError()

        line_box_top -= self.border_top
        line_box_bottom -= self.border_top
        baseline = self.content_ascent
        if self.children:
            for frame in self.children:
                frame.vertical_align(line_box_top, baseline, line_box_bottom)

    def calculate_outer_width(self):
        self.outer_width = self.content_width
        if self.border_open:
            self.outer_width += self.box.used_margin_left + \
                self.box.border_left_width + self.box.used_padding_left
        if self.border_close:
            self.outer_width += self.box.used_margin_right + \
                self.box.border_right_width + self.box.used_padding_right

    def pprint(self, indent=''):
        print '%s%s(' % (indent, self.__class__.__name__)
        print '%sborder_left=%r)' % (indent, self.border_left)
        for child in self.children:
            child.pprint(indent + '  ')

class InlineReplacedFrame(InlineFrame):
    def __init__(self, box, parent, containing_block):
        assert not box.is_text and not box.children
        super(InlineReplacedFrame, self).__init__(box, parent, containing_block)

        width = self.box.used_width
        height = self.box.used_height

        self.content_width = width
    
        self.outer_width = \
            box.used_margin_left + \
            box.border_left_width + \
            box.used_padding_left + \
            width + \
            box.used_padding_right + \
            box.border_right_width + \
            box.used_margin_right
        
        content_height = \
            box.used_margin_top + \
            box.border_top_width + \
            box.used_padding_top + \
            height + \
            box.used_padding_bottom + \
            box.border_bottom_width + \
            box.used_margin_bottom

        self.set_ascent_descent(content_height, 0, content_height, 0)

    def close(self):
        pass

    def set_border_top(self, border_top):
        self.border_top = border_top + self.box.used_margin_top
        self.border_bottom = border_top + \
            self.box.used_margin_top + \
            self.box.border_top_width + \
            self.box.used_padding_top + \
            self.box.used_height + \
            self.box.used_padding_bottom + \
            self.box.border_bottom_width

    def draw(self, render_device, x, y):
        x1 = x + self.border_left
        y1 = y - self.border_top
        x2 = x + self.border_right
        y2 = y - self.border_bottom

        self.draw_border_and_background(render_device, x1, y1, x2, y2)
        x1 += self.box.border_left_width + self.box.used_padding_left
        y1 -= self.box.border_top_width + self.box.used_padding_top
        x2 -= self.box.border_right_width + self.box.used_padding_right
        y2 += self.box.border_bottom_width + self.box.used_padding_bottom
        self.box.draw(render_device, x1, y1, x2, y2)

class TextFrame(InlineFrame):
    def __init__(self, box, parent, containing_block, 
                 from_breakpoint, to_breakpoint):
        assert box.is_text
        super(TextFrame, self).__init__(box, parent, containing_block)
        self.from_breakpoint = from_breakpoint
        self.to_breakpoint = to_breakpoint
        if from_breakpoint:
            self.border_open = False
        if to_breakpoint != None and to_breakpoint != len(box.text) - 1:
            self.border_close = False
        self.calculate_size()


    def calculate_size(self):
        if self.from_breakpoint == self.to_breakpoint:
            self.content_width = 0
        else:
            self.content_width = self.box.get_region_width(
                self.from_breakpoint, self.to_breakpoint)
        self.calculate_outer_width()
        
        ascent = self.box.intrinsic_ascent
        descent = self.box.intrinsic_descent
        if self.box.line_height != 'normal':
            half_leading = (self.box.line_height - (ascent - descent)) / 2
            inline_ascent = ascent + half_leading
            inline_descent = descent - half_leading
        else:
            inline_ascent = ascent
            inline_descent = descent
        self.set_ascent_descent(ascent, descent, inline_ascent, inline_descent)

    def close(self):
        pass

    def lstrip(self):
        '''Strip spaces from the beginning of this frame.  Conforms to
        step 1 of 16.6.1 "As each line is laid out...".'''
        text = self.box.text[self.from_breakpoint:self.to_breakpoint]
        self.from_breakpoint += len(text) - len(text.lstrip(' '))
        self.calculate_size()

    def draw(self, render_device, x, y):
        x += self.border_left
        y -= self.border_top
        self.box.draw_region(render_device, 
                             x, y - self.content_ascent, 0, 0,
                             self.from_breakpoint, self.to_breakpoint)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, 
            self.box.text[self.from_breakpoint:self.to_breakpoint])

    def pprint(self, indent=''):
        text = self.box.text[self.from_breakpoint:self.to_breakpoint]
        if len(text) > 8:
            text = '%s...' % text[:5]
        print '%s%s(%r,' % (indent, self.__class__.__name__, text)
        print '%sborder_left=%r)' % (indent, self.border_left)
        

class LineBoxFrame(InlineFrame):
    # A line box is like an anonymous block box with inline children.  It is
    # responsible for calculating line-height, remaining width (during
    # construction) and aligning elements both horizontally (text-align) and
    # vertically (vertical-align, baseline alignment).

    def __init__(self, containing_block, line_height, text_align):
        super(LineBoxFrame, self).__init__(None, None, containing_block)
        self.containing_block = containing_block
        self.line_height = line_height
        self.content_left = containing_block.left
        self.width = containing_block.width
        self.remaining_width = containing_block.width
        self.frame_width = 0

        self.text_align = text_align
        self.children = []

    def draw(self, render_device, x, y):
        x += self.content_left
        y -= self.border_top

        # XXX HACK: text looks fuzzy if not pixel-aligned.
        baseline = y - self.content_ascent
        y -= baseline - int(baseline)

        for child in self.children:
            child.draw(render_device, x, y)

    def can_add(self, frame):
        w = frame.outer_width
        if frame.border_open:
            w += frame.left_parent_bearing
        if frame.border_close:
            w += frame.right_parent_bearing
        return self.remaining_width >= w or self.frame_width == 0

    def add_descendent(self, frame):
        w = frame.outer_width
        if frame.border_open:
            w += frame.left_parent_bearing
        if frame.border_close:
            w += frame.right_parent_bearing
        self.frame_width += w
        self.remaining_width -= w

    def close(self):
        x = 0
        ascent = 0
        descent = 0
        for frame in self.children:
            frame.close()
            lx = x
            if frame.border_open:
                lx += frame.box.used_margin_left 
            frame.set_border_left(lx)

            x += frame.outer_width

            ascent = max(frame.inline_ascent, ascent)
            descent = min(frame.inline_descent, descent)

        # line-height on containing box gives minimum content height
        # of this line box.
        if self.line_height != 'normal':
            self.content_height = max(ascent - descent, self.line_height)
            half_leading = (self.content_height - (ascent - descent)) / 2
            ascent += half_leading
            descent -= half_leading
        else:
            self.content_height = ascent - descent

        self.content_ascent = ascent     # used for pixel align hack XXX

        for frame in self.children:
            frame.vertical_align(0, ascent, self.content_height)

    def set_border_top(self, border_top):
        self.border_top = border_top
        self.border_bottom = border_top + self.content_height

    def update_width(self):
        self.frame_width = sum([f.outer_width for f in self.children])
        self.frame_width += \
          sum([f.left_parent_bearing for f in self.children if f.border_open])
        self.frame_width += \
          sum([f.right_parent_bearing for f in self.children if f.border_close])
        self.remaining_width = self.containing_block.width - self.frame_width

    def create_continuation(self):
        assert not self.continuation
        self.continuation = LineBoxFrame(self.containing_block,
            self.line_height, self.text_align)

    def split(self, break_frame=None):
        super(LineBoxFrame, self).split(break_frame)
        self.update_width()
        self.continuation.update_width()

class FormattingContext(object):
    def add(self, box):
        pass

    def close(self):
        pass

class BlockFormattingContext(FormattingContext):
    # 9.4.1

    def __init__(self, containing_frame, containing_block):
        self.frame_stack = [containing_frame]
        self.containing_block_stack = [containing_block]
        self.current_margin = 0

    def add(self, box):
        assert box.display == 'block'
        frame = BlockFrame(box, self.frame_stack[0],
            self.containing_block_stack[0])
        
        # Collapse top margin
        top = self.containing_block_stack[0].content_bottom + \
              frame.box.used_margin_top
        margin = max(frame.box.used_margin_top, self.current_margin)
        top -= margin - self.current_margin

        self.frame_stack[0].add(frame)
        frame.border_top = top
        self.current_margin = margin

        self.frame_stack.insert(0, frame)
        self.containing_block_stack.insert(0, frame.generated_containing_block)

        if box.inline_formatting_context:
            context = InlineFormattingContext(self, 
                self.containing_block_stack[0],
                box.line_height)
            for child in box.children:
                context.add(child)
            context.close()
        else:
            for child in box.children:
                self.add(child)

        frame.close() # fixes border_bottom
        
        self.frame_stack.pop(0)    
        self.containing_block_stack.pop(0)

        # Collapse bottom margin
        bottom = frame.border_bottom + frame.box.used_margin_bottom
        margin = max(self.current_margin, frame.box.used_margin_bottom)
        bottom -= margin - self.current_margin
        self.containing_block_stack[0].content_bottom = bottom
        self.current_margin = margin

    def add_frame(self, frame):
        frame.parent = self.frame_stack[0]
        self.frame_stack[0].add(frame)

        frame.set_border_top(self.containing_block_stack[0].content_bottom)
        self.containing_block_stack[0].content_bottom += frame.content_height
        self.current_margin = 0

    def close(self):
        assert len(self.frame_stack) == 1

class InlineFormattingContext(FormattingContext):
    # Mostly defined by 9.4.2.

    # We don't implement the Unicode line-breaking algorithm because it's
    #  a) complex and
    #  b) not required by CSS and
    #  c) stupid (see http://www.cs.tut.fi/~jkorpela/unicode/linebr.html
    #     for a critique).
    #
    # Instead, we break by replacing any of the following characters
    # with a line-break:
    #   U+0020  SPACE
    #   U+200B  ZERO WIDTH SPACE
    #
    # Line breaks are forced at
    #   U+000A  (line feed)
    #
    # It is up to the formatter to generate boxes with these contents.
    # The formatter can do this by implementing CSS 16.6.1.

    def __init__(self, block_context, containing_block, line_height):
        self.block_context = block_context
        self.containing_block = containing_block
        self.line_box = LineBoxFrame(containing_block, line_height, 'normal')
        self.frame_stack = [self.line_box]
        self.break_frame = None
        self.break_at_end = False

    def add(self, box, space_left=0, space_right=0):
        assert box.display == 'inline'
        if box.children:
            frame = InlineFrame(box, self.frame_stack[0], self.containing_block)
            self.break_at_end = False

            # Make room for this (parent) frame's border, padding and margin
            space_left += (
                frame.box.used_margin_left +
                frame.box.used_padding_left +
                frame.box.border_left_width)
            space_right += (
                frame.box.used_margin_right +
                frame.box.used_padding_right +
                frame.box.border_right_width)

            self.frame_stack[0].add(frame)
            self.frame_stack.insert(0, frame)

            sr = 0
            for i, child in enumerate(box.children):
                if i == len(box.children) - 1:
                    sr = space_right
                self.add(child, space_left, sr)
                space_left = 0

            self.frame_stack.pop(0)
        elif box.is_text:
            text = box.get_text()
            from_breakpoint = 0

            while from_breakpoint < len(text):
                '''
                # Look for a hard line break
                if '\n' in text[from_breakpoint:]:
                    to_breakpoint = text.index('\n', from_breakpoint)
                    cbox = LineBoxRegionChild(box, from_breakpoint,
                        to_breakpoint)
                    if self.line_box.can_add(cbox):
                        self.line_box.add(cbox)
                        self.line_box.add_break_opportunity()
                        self.close_line()
                        from_breakpoint = to_breakpoint + 1
                        continue
                '''

                # Look  for a soft line break
                to_breakpoint = box.get_breakpoint(from_breakpoint, 
                    u'\u0020\u200b', 
                    self.line_box.remaining_width - space_left - space_right)
                if from_breakpoint == to_breakpoint:
                    to_breakpoint += 1
                    self.break_at_end = True
                cbox = TextFrame(box, None, self.containing_block, 
                                 from_breakpoint, to_breakpoint)
                cbox.left_parent_bearing = space_left
                cbox.right_parent_bearing = space_right

                # Step 1 of 16.6.1, "As each line is laid out.."
                # Remove leading white-space from each line.
                if (self.line_box.frame_width == 0 and 
                    box.white_space in ('normal', 'nowrap', 'pre-line')):
                    cbox.lstrip()
                    if cbox.from_breakpoint == cbox.to_breakpoint:
                        from_breakpoint = to_breakpoint
                        continue

                # If the frame won't fit on this line, and it's possible to
                # break the current line, break it.
                if not self.line_box.can_add(cbox) and \
                        (self.break_at_end or self.break_frame):
                    self.line_break()
                    continue
                
                # If this box comes after a breakpoint, set this box to be
                # the break_frame, in case a line break is needed later.
                if from_breakpoint != 0:
                    self.break_frame = cbox

                # Add this frame to the line
                self.frame_stack[0].add(cbox)
                self.line_box.add_descendent(cbox)
                cbox.parent = self.frame_stack[0]

                # If that was the last frame for the line, make sure we don't
                # break after it, and exit the loop.
                if not to_breakpoint:
                    self.break_at_end = False
                    break

                # Otherwise (more frames coming), allow a break after this
                # frame, and get ready to go again.
                self.break_at_end = True
                from_breakpoint = to_breakpoint
        else:
            # Not text (replaced element), cannot be broken.  Assume we can
            # break around it though (CSS doesn't specify).
            frame = InlineReplacedFrame(box, self.frame_stack[0],
                self.containing_block)
            # TODO left/right bearings
            if not self.line_box.can_add(frame) and \
                    (self.break_at_end or self.break_frame):
                self.line_break()
            self.frame_stack[0].add(frame)
            self.line_box.add_descendent(frame)
            self.break_at_end = True

    def line_break(self):
        assert not self.line_box.continuation

        if self.break_at_end:
            self.frame_stack[0].split(None)
        else:
            self.break_frame.parent.split(self.break_frame)
        
        self.line_box.close()
        self.block_context.add_frame(self.line_box)

        self.line_box = self.line_box.continuation

        # Adds after this line break should go into the latest continuation.
        self.frame_stack = [f.continuation or f for f in self.frame_stack]
        self.break_frame = None
        self.break_at_end = False

    def close(self):
        self.line_box.close()
        self.block_context.add_frame(self.line_box)

class VisualLayout(object):
    def __init__(self, render_device):
        self.render_device = render_device
        self.frame = None

    def draw(self):
        self.draw_viewport(0, 0, 
            self.render_device.width, self.render_device.height)

    def draw_viewport(self, 
                      viewport_left, viewport_top, 
                      viewport_right, viewport_bottom):
        self.frame.draw(self.render_device, 0, 0)

    def hit_test(self, x, y):
        pass

    # Layout processing
    # -----------------

    def set_root(self, box):
        self.root_box = box

    def layout(self):
        # Not specified in CSS spec, we're going to force it.  Shouldn't
        # make any difference block/inline.  Other options don't make much
        # sense.  TODO Could create an anonymous block box if necessary.
        self.root_box.display = 'block'

        self.frame = ViewportFrame()
        context = BlockFormattingContext(
            self.frame, self.initial_containing_block())
        context.add(self.root_box)
        context.close()
        #self.frame.pprint()
    
    def initial_containing_block(self):
        return ContainingBlock(0, 0, 
            self.render_device.width, 
            self.render_device.height)


