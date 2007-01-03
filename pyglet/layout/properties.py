#!/usr/bin/env python

'''Description, parsing and validation of CSS 2.1 properties.

These are the specific properties described in CSS 2.1 that apply to XML,
XHTML and HTML documents.

There are functions for applying CSS properties (declarations) to a layout
box.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from warnings import *

from pyglet.layout.css import *

def apply_style_declarations(declarations, box, render_device):
    '''Apply the given list of declarations to the given box.

    The render device is required in order to convert dimensions into device
    units.  Invalid values are ignored with a warning.
    '''
    for declaration in declarations:
        if declaration.property in _properties:
            attr, inheritable, multivalue, parse_func = \
                _properties[declaration.property]
            if not multivalue:
                if len(declaration.values) != 1:
                    continue
                value = declaration.values[0]
            else:
                value = declaration.values

            if (inheritable and 
                isinstance(value, Ident) and
                value == 'inherit' and
                box.parent):
                if type(attr) in (list, tuple):
                    for a in attr:
                        setattr(box, a, getattr(box.parent, a))
                else:
                    setattr(box, attr, getattr(box.parent, attr))
            else:
                try:
                    value = parse_func(value, render_device)
                    if type(attr) in (list, tuple):
                        for a, v in zip(attr, value):
                            setattr(box, a, v)
                    else:
                        setattr(box, attr, value)
                except ValidationException:
                    warnings.warn(
                        'CSS validation error in %s' % declaration.property)


def apply_inherited_style(box):
    '''Allow the box to inherit inherited properties from its parent.'''
    if not box.parent:
        return
    d = box.parent.__dict__
    for attr in _inherited_properties:
        if attr in d:
            setattr(box, attr, d[attr])

def apply_stylesheet(stylesheet, elem, box, render_device):
    '''Apply the given Stylesheet object to the given box.

    'elem' is an instance of SelectableElement and is required for corrent
    selector matching.
    '''
    declarations = stylesheet.get_declarations(elem)
    apply_style_declarations(declarations, box, render_device)


class ValidationException(Exception):
    pass

def _parse_generic(*args):
    # Accept any given type or ident.
    def f(value, render_device):
        if type(value) in args or \
           (type(value) in (Ident, Number) and value in args):
            return value
        else:
            raise ValidationException()
    return f

def _parse_shortcut(value_parser):
    # Parse shortcut properties that depend on the number of arguments:
    # 1: top/right/bottom/left
    # 2: top/bottom left/right
    # 3: top, left/right, bottom
    # 4: top, right, bottom, left
    def f(value, render_device):
        value = [value_parser(v, render_device) for v in value]
        if len(value) == 1:
            return value[0], value[0], value[0], value[0]
        elif len(value) == 2:
            return value[0], value[1], value[0], value[1]
        elif len(value) == 3:
            return value[0], value[1], value[2], value[1]
        elif len(value) == 4:
            return value
        else:
            raise ValidationException()
    return f

def _parse_color(value, render_device):
    if isinstance(value, Ident):
        if value in Color.names:
            return Color.names[value]
        else:
            raise ValidationException()
    elif isinstance(value, Color):
        return value
    else:
        raise ValidationException()

def _parse_transparent_color(value, render_device):
    if isinstance(value, Ident) and value == 'transparent':
        return value
    else:
        return _parse_color(value, render_device)

def _parse_border_shortcut(count):
    def f(value, render_device):
        width = 2
        style = Ident('none')
        color = None
        for v in value:
            if isinstance(v, Dimension):
                width = _parse_border_width(v, render_device)
            elif v in ['none', 'hidden', 'dotted', 'dashed', 'solid',
                       'double', 'groove', 'ridge', 'inset', 'outset']:
                style = _parse_border_style(v, render_device)
            else:
                color = _parse_transparent_color(v, render_device)

        return [width, style, color] * count
    return f

def _parse_border_width(value, render_device):
    if isinstance(value, Ident):
        if value == 'thin':
            return Dimension('1px')
        elif value == 'medium':
            return Dimension('2px')
        elif value == 'thick':
            return Dimension('4px')
        else:
            raise ValidationException()
    elif isinstance(value, Dimension):
        return value
    elif value == 0:
        return 0
    else:
        raise ValidationException()

def _parse_font_family(value, render_device):
    # Remove commas from list
    for v in value[1::2]:
        if v != ',':
            raise ValidationException()
    return value[::2]

_parse_margin = _parse_generic(Dimension, Percentage, 'auto', 0)
_parse_padding = _parse_generic(Dimension, Percentage, 'auto', 0)
_parse_line_height = _parse_generic(Number, Dimension, Percentage, 'normal')
_parse_font_size = _parse_generic(Dimension, Number, Percentage,
    'xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large')

_parse_vertical_align = _parse_generic(
    Percentage, Dimension, 
    'baseline', 'sub', 'super', 'top', 'text-top', 'middle', 'bottom',
    'text-bottom')
    
_parse_border_style = _parse_generic(
    'none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove',
    'ridge', 'inset', 'outset') 

_properties = {
#    CSS name,              Box attr,        
#       inhrtble, multivalue, parse function
    'background-color':     ('background_color',    
        True,   False,  _parse_transparent_color),
    'background-image':     ('background_image',
        True,   False,  _parse_generic(URI, 'none')),
    'background-repeat':    ('background_repeat',
        True,   False,  _parse_generic(
            'repeat', 'repeat-x', 'repeat-y', 'no-repeat')),
    'border':               (
        ['border_top_width', 'border_top_style', 'border_top_color',
         'border_right_width', 'border_right_style', 'border_right_color',
         'border_bottom_width', 'border_bottom_style', 'border_bottom_color',
         'border_left_width', 'border_left_style', 'border_left_color'],
        True,   True,   _parse_border_shortcut(4)),
    'border-top':           (
        ['border_top_width', 'border_top_style', 'border_top_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-right':           (
        ['border_right_width', 'border_right_style', 'border_right_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-bottom':           (
        ['border_bottom_width', 'border_bottom_style', 'border_bottom_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-left':           (
        ['border_left_width', 'border_left_style', 'border_left_color'],
        True,   True,   _parse_border_shortcut(1)),
    'border-color':         (
        ['border_top_color', 'border_right_color', 'border_bottom_color',
         'border_left_color'],
        True,   True,   _parse_shortcut(_parse_transparent_color)),
    'border-top-color':     ('border_top_color',
        True,   False,  _parse_transparent_color),
    'border-right-color':   ('border_right_color',
        True,   False,  _parse_transparent_color),
    'border-bottom-color':  ('border_bottom_color',
        True,   False,  _parse_transparent_color),
    'border-left-color':    ('border_left_color',
        True,   False,  _parse_transparent_color),
    'border-style':         (
        ['border_top_style', 'border_right_style', 'border_bottom_style',
         'border_left_style'],
        True,   True,   _parse_shortcut(_parse_border_style)),
    'border-top-style':     ('border_top_style',    
        True,   False,  _parse_border_style),
    'border-right-style':   ('border_right_style',  
        True,   False,  _parse_border_style),
    'border-bottom-style':  ('border_bottom_style', 
        True,   False,  _parse_border_style),
    'border-left-style':    ('border_left_style',   
        True,   False,  _parse_border_style),
    'border-width':         (
        ['border_top_width', 'border_right_width', 'border_bottom_width',
         'border_left_width'],
        True,   True,   _parse_shortcut(_parse_border_width)),
    'border-top-width':     ('border_top_width',    
        True,   False,  _parse_border_width),
    'border-right-width':   ('border_right_width',  
        True,   False,  _parse_border_width),
    'border-bottom-width':  ('border_bottom_width', 
        True,   False,  _parse_border_width),
    'border-left-width':    ('border_left_width',   
        True,   False,  _parse_border_width),
    'bottom':               ('bottom',
        True,   False,  _parse_generic(Dimension, Percentage, 'auto')),
    'color':                ('color',               
        True,   False,  _parse_color),
    'display':              ('display',             
        True,   False,  _parse_generic(
            'inline', 'block', 'list-item', 'run-in', 'inline-block',
            'table', 'inline-table', 'table-row-group', 'table-header-group',
            'table-footer-group', 'table-row', 'table-column-group',
            'table-cell', 'table-caption', 'none')),
    'font-family':          ('font_family',         
        True,   True,   _parse_font_family),
    'font-size':            ('font_size',           
        True,   False,  _parse_font_size),
    'font-style':           ('font_style',
        True,   False,  _parse_generic('normal', 'italic', 'oblique')),
    'font-weight':          ('font_weight',
        True,   False,  _parse_generic(Number, 
            'normal', 'bold', 'bolder', 'lighter')),
    'height':               ('height',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'auto')),
    'left':                  ('left',
        True,   False,  _parse_generic(Dimension, Percentage, 'auto')),
    'line-height':          ('line_height',
        True,   False,  _parse_line_height),
    'margin':               (
        ['margin_top', 'margin_right', 'margin_bottom', 'margin_left'],
        True,   True,   _parse_shortcut(_parse_margin)),
    'margin-top':           ('margin_top',          
        True,   False,  _parse_margin),
    'margin-right':         ('margin_right',
        True,   False,  _parse_margin),
    'margin-bottom':        ('margin_bottom',
        True,   False,  _parse_margin),
    'margin-left':          ('margin_left',
        True,   False,  _parse_margin),
    'max-height':           ('max_height',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'none')),
    'max-width':            ('max_width',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'none')),
    'min-height':            ('min_height',
        True,   False,  _parse_generic(Dimension, Percentage, 0)),
    'min-width':            ('min_width',
        True,   False,  _parse_generic(Dimension, Percentage, 0)),
    'padding':              (
        ['padding_top', 'padding_right', 'padding_bottom', 'padding_left'],
        True,   True,   _parse_shortcut(_parse_padding)),
    'padding-top':          ('padding_top',
        True,   False,  _parse_padding),
    'padding-right':        ('padding_right',
        True,   False,  _parse_padding),
    'padding-bottom':       ('padding_bottom',
        True,   False,  _parse_padding),
    'padding-left':         ('padding_left',
        True,   False,  _parse_padding),
    'position':             ('position',            
        True,   False,  _parse_generic(
            'static', 'relative', 'absolute', 'fixed')),
    'right':                  ('right',
        True,   False,  _parse_generic(Dimension, Percentage, 'auto')),
    'top':                  ('top',
        True,   False,  _parse_generic(Dimension, Percentage, 'auto')),
    'vertical-align':       ('vertical_align',
        True,   False,  _parse_vertical_align),
    'white-space':          ('white_space',
        True,   False,  _parse_generic(
            'normal', 'pre', 'nowrap', 'pre-wrap', 'pre-line')),
    'width':                ('width',
        True,   False,  _parse_generic(Dimension, Percentage, 0, 'auto'))
}

# Properties that are inherited by default, as listed in Appendix F (visual,
# non-page only).
_inherited_properties = [
    'border_collapse',
    'border_spacing',
    'caption_side',
    'color',
    'cursor',
    'direction',
    'empty_cells',
    'font_family',
    'font_size',
    'font_style',
    'font_variant',
    'font_weight',
    'letter_spacing',
    'line_height',
    'list_style_image',
    'list_style_position',
    'list_style_type',
    'quotes',
    'text_align',
    'text_indent',
    'text_transform',
    'visibility',
    'white_space',
    'word_spacing',
]


