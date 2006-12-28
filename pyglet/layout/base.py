#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


#-----------------------------------------------------------------------------
# Basic types.  Some (AtKeyword, Hash, CDO, CDC, Whitespace, Function,
# Delim) are used only by the CSS parser.  The rest are used both by
# the parser and within Box objects to represent values.  Some values
# are converted during parsing (specified values, e.g., Hash to Color), some
# are converted during formatting (computed values, e.g., Ident('inherit'),
# length unit reduction), and some during layout (used values, e.g., used
# Percentage).

class Ident(str):
    def __new__(cls, text):
        return str.__new__(cls, text.lower())

class AtKeyword(str):
    def __new__(cls, text):
        return str.__new__(cls, text.lower())

class String(str):
    def __new__(cls, text):
        return str.__new__(cls, text[1:-1])

class Hash(str):
    def __new__(cls, text):
        return str.__new__(cls, text[1:])

class Number(float):
    def __neg__(self):
        n = float.__new__(self.__class__, -float(self))
        return n

class Percentage(float):
    def __new__(cls, text):
        return float.__new__(cls, text[:-1])

    def __neg__(self):
        n = float.__new__(self.__class__, -float(self))
        return n

class Dimension(float):
    def __new__(cls, text):
        unit = text.lstrip('0123456789.')
        num = text[:-len(unit)]
        n = float.__new__(cls, num)
        n.unit = unit.lower()
        return n

    def __neg__(self):
        n = float.__new__(self.__class__, -float(self))
        n.unit = self.unit
        return n

class URI(str):
    pass

class UnicodeRange(str):
    pass

class CDO(object):
    pass

class CDC(object):
    pass

class Whitespace(object):
    pass

class Function(str):
    pass

class Delim(str):
    pass

class Important(object):
    pass

class Color(tuple):
    def __new__(cls, r, g, b, a=1):
        return tuple.__new__(cls, (r, g, b, a))

    @classmethod
    def from_hex(cls, hex):
        if len(hex) == 3:
            return Color(int(hex[0], 16) / 15., 
                         int(hex[1], 16) / 15.,
                         int(hex[2], 16) / 15.)
        else:
            return Color(int(hex[0:2], 16) / 255.,
                         int(hex[2:4], 16) / 255.,
                         int(hex[4:6], 16) / 255.)

# 4.3.6 Color keywords
Color.names = {
    'maroon':   Color.from_hex('800000'),
    'red':      Color.from_hex('ff0000'),
    'orange':   Color.from_hex('ffa500'),
    'yellow':   Color.from_hex('ffff00'),
    'olive':    Color.from_hex('808000'),
    'purple':   Color.from_hex('800080'),
    'fuschia':  Color.from_hex('ff00ff'),
    'white':    Color.from_hex('ffffff'),
    'lime':     Color.from_hex('00ff00'),
    'green':    Color.from_hex('008000'),
    'navy':     Color.from_hex('000080'),
    'blue':     Color.from_hex('0000ff'),
    'aqua':     Color.from_hex('00ffff'),
    'teal':     Color.from_hex('008080'),
    'black':    Color.from_hex('000000'),
    'silver':   Color.from_hex('c0c0c0'),
    'gray':     Color.from_hex('808080'),
}

#-----------------------------------------------------------------------------


class Box(object):
    # Layout engine properties
    # ------------------------

    # children can optionally be None to represent the empty list.  This
    # should be populated by box creation before handing over to the layout
    # engine.
    children = None

    # parent is None only for the root box.
    parent = None

    # Formatting context can either be inline or block.  Inline context
    # only contains inline boxes (and floats, absolutes, etc.).  Block
    # context only contains block boxes (etc).  It is up to the formatter to
    # ensure this is true, and create anonymous block boxes where necessary.  
    # See 9.2.
    inline_formatting_context = True

    # Subclasses which are not text _must_ override this with True;
    # it enables replaced-element processing, including the intrinsic
    # properties below.
    is_replaced = False

    # intrinsic_width must be set for replaced and non-replaced (text)
    # elements.  intrinsic_height is set only for replaced elements.      
    # A replaced element such as an image would give the dimensions of the
    # image here, even though it could be stretched by the width/height
    # attributes.  The intrinsic ratio (see 10.4) is calculated from these
    # values when needed.
    intrinsic_width = 0
    intrinsic_height = 0

    # For replaced elements (text) only, in place of intrinsic_height.
    # intrinsic_descent is typically negative (below the baseline).
    intrinsic_ascent = 0
    intrinsic_descent = 0

    # This references a box which implements a box's :first-line
    # pseudo-element.  Note that pseudo-classes are resolved
    # at box creation time, as are the :first-letter, :before and :after
    # pseudo-elements.
    pseudo_first_line = None

    # These give the box's layout position, ready for rendering.  They
    # refer to the content edge.
    content_left = 0
    content_top = 0
    content_right = 0   # right, bottom not always calculated.
    content_bottom = 0

    # Box-specific functionality
    # --------------------------

    # If true, this box is an anonymous block box (see 9.2.1) and can
    # accept additional inline boxes.
    anonymous = False

    # Text-wrapping functionality
    # ---------------------------
    # If `is_text` is True, all must be implemented.  Otherwise,
    # none are implemented (the box will not be split).  

    # If is_text is False, box can wrap onto a new line without splitting.
    # Otherwise, the following methods are used to determine valid
    # breakpoints within the box, and the box is not wrapped by default.
    is_text = False

    def get_text(self):
        return None

    def get_breakpoint(self, from_breakpoint, break_characters, width):
        '''Return a breakpoint index that occurs after `from_breakpoint`
        but before `width` pixels, that is greater than all other possible
        breakpoints that match the same criteria.  The breakpoint 
        occurs at a character from the set of characters `break_characters`.
        Return None if no breakpoints are possible.
        '''
        return None

    def get_region_width(self, from_breakpoint, to_breakpoint):
        '''Return the amount of horizontal space, in pixels, required to
        draw the given region defined by the breakpoints.  Either breakpoint
        may be None, representing the beginning or end of the box.'''
        return 0

    def draw_region(self, render_context, x, y, from_breakpoint, to_breakpoint):
        '''Draw the region of this box defined by the two breakpoints
        (as returned by `get_breakpoint`).  Either breakpoint may be
        None, representing the beginning or end of the box.'''
        pass

    # Debug
    # -----

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__dict__)

    # CSS 2.1 properties
    # ------------------

    # 8 Box model
    # 8.3 Margin properties
    margin_top = 0
    margin_bottom = 0
    margin_right = 0
    margin_left = 0
    # Used values for margin properties (calculated during layout)
    used_margin_top = 0
    used_margin_bottom = 0
    used_margin_right = 0
    used_margin_left = 0
    # 8.4 Padding properties
    padding_top = 0
    padding_bottom = 0
    padding_right = 0
    padding_left = 0
    # Used values for margin properties (calculated during layout)
    used_padding_top = 0
    used_padding_bottom = 0
    used_padding_right = 0
    used_padding_left = 0
    # 8.5.1 Border width
    border_top_width = 2       # default to 'medium' if style != 'none'
    border_right_width = 2     # default to 'medium' if style != 'none'
    border_bottom_width = 2    # default to 'medium' if style != 'none'
    border_left_width = 2      # default to 'medium' if style != 'none'
    # 8.5.2 Border color
    border_top_color = None     # default to self.color
    border_right_color = None   # default to self.color
    border_bottom_color = None  # default to self.color
    border_left_color = None    # default to self.color
    # 8.5.3 Border style
    border_top_style = Ident('none')
    border_right_style = Ident('none')
    border_bottom_style = Ident('none')
    border_left_style = Ident('none')

    # 9 Visual formatting model
    # 9.2.4 The 'display' property
    # 'run-in' display must be resolved during box creation; the value
    # is not permitted in layout.
    display = Ident('inline')
    # 9.3.1 Choosing a positioning scheme: 'position' property
    position = Ident('static')
    # 9.3.2 Box offsets
    # Applies only to positioned elements (position != 'static')
    top = Ident('auto')
    right = Ident('auto')
    bottom = Ident('auto')
    left = Ident('auto')
    # 9.5.1 Positioning the float
    float = Ident('none')
    # 9.5.2 Controlling flow next to floats
    # Applies only to block-level elements
    clear = Ident('none')
    # 9.9.1 Specifying the stack level
    # Applies only to positioned elements
    z_index = Ident('auto')
    # 9.10 Text direction
    direction = Ident('ltr')
    unicode_bidi = Ident('normal')

    # 10 Visual formatting model details
    # 10.2 Content width
    width = Ident('auto')
    # 10.4 Minimum and maximum widths
    min_width = 0
    max_width = Ident('none')
    # 10.5 Content height
    height = Ident('auto')
    # 10.7 Minimum and maximum heights
    min_height = 0
    max_height = Ident('none')
    # 10.8 Line height calculations
    line_height = Ident('normal')

    # 11 Visual effects
    # 11.1.1 Overflow
    # Applies to non-replaced block-level elements, table cells and
    # inline-block elements
    overflow = Ident('visible')
    # 11.1.2 Clipping
    clip = Ident('auto')
    # 11.2 Visibility
    visibility = Ident('visible')
    # Applies to inline-level and 'table-cell' elements
    vertical_align = Ident('baseline')

    # 12 Generated content, automatic numbering, and lists
    # 12.2 The 'content' property
    # content, counters and quotes are not implemented here, performed
    # at box construction level.
    # 12.5.1 Lists
    # list-style-type is implemented at box construction level.
    list_style_image = Ident('none')
    # Applies to 'list-item' elements
    list_style_position = Ident('outside')

    # 13 Paged media
    # Page break properties are ignored by pyglet.layout.

    # 14 Colors and Backgrounds
    # 14.1 Foreground color
    color = Color.names['black']     # Initial value is up to UA
    # 14.2.1 Background properties
    background_color = Ident('transparent')
    background_image = Ident('none')
    background_repeat = Ident('repeat')
    background_attachment = Ident('scroll')
    background_position = (0, 0)

    # 15 Fonts
    # 15.3 Font family
    font_family = None  # Depends on UA
    # 15.4 Font styling
    font_style = Ident('normal')
    # 15.5 Small-caps
    font_variant = Ident('normal')
    # 15.6 Font boldness
    font_weight = Ident('normal')
    # 15.7 Font size
    font_size = Ident('medium')

    # 16 Text
    # 16.1 Indentation
    # Applies to block-level elements, table cells and inline blocks
    text_indent = 0
    # 16.2 Alignment
    # left if 'direction' is 'ltr', 'right' if 'direction is 'rtl'
    text_align = None   
    # 16.3 Decoration
    text_decoration = Ident('none')
    # 16.4 Letter and word spacing
    letter_spacing = Ident('normal')
    word_spacing = Ident('normal')
    # 16.5 Capitalization
    text_transform = Ident('none')
    # 16.6 Whitespace
    # Steps 1-4 of 16.6.1 must be executed in formatter; layout engine only
    # performs steps beginning "As each line is laid out,".
    white_space = Ident('normal')

    # 17 Tables
    # 17.4.1 Caption position and alignment
    # Applies to table-caption elements
    caption_side = Ident('top')
    # 17.5.2 Table width algorithms
    table_layout = Ident('auto')
    # 17.6 Borders
    # Applies to 'table' and 'inline-table' elements
    border_collapse = Ident('separate')
    # Applies to 'table' and 'inline-table' elements
    border_spacing = 0
    # 17.6.1.1 Borders and Backgrounds around empty cells
    # Applies to 'table-cell' elements
    empty_cells = Ident('show')

