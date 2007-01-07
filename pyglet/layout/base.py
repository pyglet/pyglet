#!/usr/bin/env python

'''Base layout types and interfaces.

Section numbers refer to the CSS 2.1 specification at 
http://www.w3.org/TR/CSS21/
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


#-----------------------------------------------------------------------------
# Basic types.  These are used both by the scanner/parser and within the
# Box and Frame types to represent CSS property values.

class Ident(str):
    '''An unquoted string, such as a colour name or XML element name.'''
    def __new__(cls, text):
        # XXX: This should not generally be lowercased, as it applies to
        #      XML element names.  However, property values like colour names
        #      must be compared case insensitively.  TODO: lowercase at the
        #      at the appropriate comparison point instead of here.
        return str.__new__(cls, text.lower())


class String(str):
    '''A quoted string, without the quotes.  Escapes should have already been
    processed.'''
    def __new__(cls, text):
        return str.__new__(cls, text[1:-1])


class Number(float):
    '''A floating-point number without dimension.'''
    def __neg__(self):
        n = float.__new__(self.__class__, -float(self))
        return n

class Percentage(float):
    '''A percentage, expressed as float in range [0,1].'''
    def __new__(cls, text):
        return float.__new__(cls, float(text[:-1]) / 100.)

    def __neg__(self):
        n = float.__new__(self.__class__, -float(self))
        return n

class Dimension(float):
    '''A dimension with unit, such as 'px', 'em' or 'in'. 
    
    Units are not checked by the parser for correctness.  Units are always
    lowercase.  This value is a float with a 'unit' attribute, which is a
    string.  All numeric operations except for unary negate will return floats
    instead of Dimension instances.
    '''
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
    '''A URI, such as http://pyglet.org.  Does not include formatting
    tokens such as uri(...).'''
    def __new__(cls, text):
        # TODO wrong wrong wrong
        return str.__new__(cls, text[4:-1].strip())

class UnicodeRange(str):
    '''A Unicode range, such as U+1000-1500, expressed as a complete string.
    '''
    pass

class Color(tuple):
    '''An RGBA tuple, with each component in range [0,1].  CSS 2.1 has no
    alpha support, so the alpha channel is typically 1.0.'''
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

# Interfaces
# ----------------------------------------------------------------------------

class RenderDevice(object):
    '''Interface for device to render layout to.

    The render device defines properties such as the media width and height
    (which may be a scrollable viewport), the DPI and related metrics, and
    conversions between named font sizes and their point size (which may be
    altered at run-time by the user agent).

    The render device also contains methods which the layout uses to
    draw the rendered image.  A render device need only implement the methods
    it wants to support; for example, not implementing the border methods
    means borders will not be drawn (but will still be accounted for in
    layout).  The text and font retrieval methods must be implemented.
    '''
    # Physical resolution of the device.  The default units are recommended
    # for standard computer displays (a printer would have a much higer DPI
    # and PPD, though).
    dpi = 96            # device units per in
    ppd = 1             # px per device unit
    ppi = ppd * dpi     # calculated px per in

    # Lookup dictionary for named font sizes.  By default text is rendered at
    # 'medium' size.
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
        '''Return a dimension for the given named font size (for example,
        'medium').  This can be overridden by user agents to allow the text
        size to be increased or decreased.'''
        return self.font_sizes[name]

    def dimension_to_pt(self, dimension):
        '''Convert the given dimension to a dimension in points.  
        
        The default implementation uses the 'dpi' and 'ppi' constants on the
        class.'''
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
        '''Convert the given dimension to device units.  
        
        Device units are the same as pixels on a computer monitor, but on a
        printer more device units are typically used in order to keep the
        physical size reasonable for pixel-based layouts.  The default
        implementation uses the 'dpi' and p'pi' constants on the class.  
        
        The font-size argument must be the relevant box's font size, as a
        dimension in points.  This is used to calculate the relative sizes
        "em" and "ex" correctly.  The "relevant" box is typically the one
        which contains the property which is currently being evaluated, or its
        parent if the property is the font-size.
        '''
        if dimension.unit == 'px':
            return dimension / self.ppd
        elif dimension.unit == 'in':
            return dimension * self.dpi
        elif dimension.unit == 'pt':
            return dimension / 72. * self.dpi
        elif dimension.unit == 'pc':
            return dimension / 12. / 72. * self.dpi
        elif dimension.unit == 'em':
            assert font_size.unit == 'pt'
            return dimension * font_size / 72. * self.dpi
        elif dimension.unit == 'ex':
            assert font_size.unit == 'pt'
            return dimension * font_size / 2 / 72. * self.dpi # guess only
        elif dimension.unit == 'cm':
            return dimension / 2.54 * self.dpi
        elif dimension.unit == 'mm':
            return dimension / 10. / 2.54 * self.dpi
        else:
            raise NotImplementedError

    def draw_vertical_border(self, x1, y1, x2, y2, color, style):
        '''Draw a vertical border within the given bounds.  'color' is
        an RGB tuple and 'style' is the CSS border-style property, which will
        not be 'none'.
        '''
        pass

    def draw_horizontal_border(self, x1, y1, x2, y2, color, style):
        '''Draw a horizontal border within the given bounds.  'color' is
        an RGB tuple and 'style' is the CSS border-style property, which will
        not be 'none'.
        '''
        pass

    def draw_background(self, x1, y1, x2, y2, box):
        '''Fill the given region with the box background, which may be
        the background-color or background-image as appropriate.
        '''
        pass

    def set_clip(self, left, top, right, bottom):
        '''Currently unused, but in future will be used to set clipping
        regions on the render device in order to implement the overflow
        property.'''
        pass

    def get_font(self, box):
        '''Return a font object for the given box.  
        
        The font object must encapsulate all information about the font-face,
        font-size and font-style of the box, but not color, text-decoration,
        text-transform, word or character spacing.

        Fonts are not cached by layout, it is recommended that the render
        device does this.
        '''
        raise NotImplementedError('abstract')

    def create_text_frames(self, font, text, width, break_characters):
        '''Return zero or more text frames

        The font paramter is a return value from 'get_font'.
        '''
        raise NotImplementedError('abstract')

class Formatter(object):
    '''Interface for formatters: objects that create CSS boxes from some data
    (e.g. XHTML).'''
    def __init__(self, render_device):
        self.render_device = render_device
        self.generators = {}

    def format(self, data):
        '''Format the given data, which may be a string or file-like object,
        and return the root Box element.'''
        raise NotImplementedError('abstract')

    def add_generator(self, generator):
        '''Add a custom box generator to this formatter.  Only one generator
        can be associated with a given element name (an assertion will be
        raised if not).
        '''
        for name in generator.accept_names:
            assert name not in self.generators
            self.generators[name] = generator

class BoxGenerator(object):
    '''Interface for box generators: objects that boxes for data, controlled
    by a formatter.  
    
    For example, a BoxGenerator is defined to create replaced element boxes
    for images in an XHTML formatter.'''

    # List of element names this generator will generate boxes for.  For
    # example, ['img'] for image elements in XHTML. 
    accept_names = []

    def create_box(self, name, attrs):
        '''Create a box for the given element name and attributes.  
        
        The exact meaning of name and attrs are defined by the formatter, but
        name must be a string from the 'accept_names' list, and 'attrs' a
        dictionary-like object.
        
        Must return a single Box object.
        ''' 
        raise NotImplementedError('abstract')


class Box(object):
    '''A CSS box.

    Non-replaced elements besides non-replaced inline elements use this
    class directly.  All other elements (non-replaced inline elements and
    replaced elements) subclass.

    Every CSS property is defined on every box.  This is necessary to 
    ensure properties are inherited correctly.  To save on memory usage,
    the intial values are stored on the class where possible.  
    
    The values applied on a Box object are the "specified" or "computed"
    values (depending on the stage of processing), never the "used" or
    "actual" values (though those values may be implicitly identical).

    In addition to the CSS properties there are several "layout engine
    properties" which exist for the convenience of the formatter and
    are not specified explicitly in CSS declarations, and "replaced element
    properties", which must be supplied by the box generator.

    There are draw methods that correspond to replaced and non-replaced
    inline element boxes (non-replaced non-inline boxes are never drawn --
    only their borders/backgrounds are, handled by the frame).

    To implement a custom replaced element, subclass Box and set the
    appropriate replaced element properties.  Then override the simple
    'draw' method (not the text draw method).
    '''

    # Replaced element properties
    # ---------------------------

    # Subclasses which are not text _must_ override this with True;
    # it enables replaced-element processing, including the intrinsic
    # properties below.
    is_replaced = False

    # intrinsic_width must be set for non-replaced (text) elements, and may be
    # set for replaced elements.  intrinsic_height is set only for replaced
    # elements.  A replaced element such as an image would give the
    # dimensions of the image here, even though it could be stretched by the
    # width/height properties.  The intrinsic ratio can also be set.
    intrinsic_width = None
    intrinsic_height = None 
    intrinsic_ratio = None

    def draw(self, render_device, left, top, right, bottom):
        '''Draw a replaced element at the given position.  Note that
        the default visual layout has vertical coordinates increasing towards
        the top of the screen.'''
        pass

    # Layout engine properties
    # ------------------------

    # The element (SelectableElement or subclass) that generated this
    # box
    element = None

    # A box can have either children or text, but not both.  Use anonymous
    # inline boxes to add children to boxes which already have text, or
    # to add text to boxes that already have children.
    children = ()       # list of Box
    text = ''           # str or unicode

    # parent is None only for the root box.
    parent = None

    # Formatting context can either be inline or block.  Inline context
    # only contains inline boxes (and floats, absolutes, etc.).  Block
    # context only contains block boxes (etc).  It is up to the formatter to
    # ensure this is true, and create anonymous block boxes where necessary.  
    # See 9.2.
    inline_formatting_context = True

    # If true, this box is an anonymous block box (see 9.2.1) and can
    # accept additional inline boxes.
    anonymous = False

    # Debug
    # -----

    def __repr__(self):
        d = self.__dict__.copy()
        d['children'] = self.children and len(self.children)
        if 'parent' in d:
            del d['parent']
        return '%s(%r)' % (self.__class__.__name__, d)

    # CSS 2.1 properties
    # ------------------

    # 8 Box model
    # 8.3 Margin properties
    margin_top = 0
    margin_bottom = 0
    margin_right = 0
    margin_left = 0
    # 8.4 Padding properties
    padding_top = 0
    padding_bottom = 0
    padding_right = 0
    padding_left = 0
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
    font_weight = 400
    # 15.7 Font size
    font_size = Ident('medium')

    # Above combines to give computed font object, resolved by formatter.
    font = None

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

