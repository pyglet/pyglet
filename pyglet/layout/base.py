#!/usr/bin/env python

'''Base layout types and interfaces.

Section numbers refer to the CSS 2.1 specification at 
http://www.w3.org/TR/CSS21/
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


#-----------------------------------------------------------------------------
# Basic types.  These are used both by the scanner/parser and within the
# style tree.

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

    def draw_vertical_border(self, x1, y1, x2, y2, x3, y3, x4, y4, 
                             color, style):
        '''Draw a vertical border within the given bounds.  'color' is
        an RGB tuple and 'style' is the CSS border-style property, which will
        not be 'none'.

        Order of vertices is inner-top, inner-bottom, outer-bottom, outer-top
        '''
        pass

    def draw_horizontal_border(self, x1, y1, x2, y2, x3, y3, x4, y4, 
                             color, style):
        '''Draw a horizontal border within the given bounds.  'color' is
        an RGB tuple and 'style' is the CSS border-style property, which will
        not be 'none'.

        Order of vertices is inner-left, inner-right, outer-right, outer-left.
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

    def get_font(self, names, size, style, weight):
        '''Return a font object for the given attributes.  
        
        The font object must encapsulate all information about the font-face,
        font-size and font-style of the box, but not color, text-decoration,
        text-transform, word or character spacing.

        Fonts are not cached by layout, it is recommended that the render
        device does this.
        '''
        raise NotImplementedError('abstract')

    def create_text_frame(self, style, element, text):
        '''Return an unstyled text frame.
        '''
        raise NotImplementedError('abstract')

