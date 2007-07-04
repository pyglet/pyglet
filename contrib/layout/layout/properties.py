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

from layout.base import *
from layout.css import *

class StyleTree(object):
    def __init__(self, render_device):
        self.children = {}
        self.render_device = render_device
        self.default_node = StyleNode(None, DeclarationSet(()), render_device)

    def get_style_node(self, declaration_sets):
        if not declaration_sets:
            return self.default_node
        nodes = self.children
        node = None
        for declaration_set in declaration_sets:
            if declaration_set in nodes:
                node = nodes[declaration_set]
                nodes = node.children
            else:
                node = StyleNode(node, declaration_set, self.render_device)
                nodes[declaration_set] = node
                nodes = node.children
        return node


_compute_functions = {}
def css(*properties):
    def f(func):
        for property in properties:
            _compute_functions[property] = func
        return func
    return f

class StyleNode(object):
    def __init__(self, parent, declaration_set, render_device):
        self.parent = parent
        self.children = {}
        self.render_device = render_device

        self.specified_properties = {}
        for declaration in declaration_set.declarations:
            for attr, value in validate_declaration(declaration):
                attr = attr.replace('_', '-') #HACK XXX
                self.specified_properties[attr] = value
        self.computed_properties = {}

    def get_specified_property(self, property):
        # Search up style tree for validated property; if not found
        # return initial value (or 'inherit')
        style = self
        while style:
            if property in style.specified_properties:
                return style.specified_properties[property]
            style = style.parent

        if property.replace('-', '_') in _inherited_properties: #HACK XXX
            return Ident('inherit')
        else:
            return _initial_values[property]

    def get_computed_property(self, property, frame):
        # Check node cache for frame invariant result
        if property in self.computed_properties:
            return self.computed_properties[property]

        # Check frame cache for precomputed result
        if property in frame.computed_properties:
            return frame.computed_properties[property]

        # Nothing cached, work it out.
        specified = self.get_specified_property(property)
        if type(specified) == Ident and specified == 'inherit':
            result = self.get_inherited_property(property, frame)
            node_cacheable = False
        elif property in StyleNode._compute_functions:
            func = StyleNode._compute_functions[property]
            result, node_cacheable = func(self, property, specified, frame)
        else:
            # Computed as specified
            result = specified
            node_cacheable = True

        if node_cacheable:
            self.computed_properties[property] = result
        else:
            frame.computed_properties[property] = result

        return result

    def get_inherited_property(self, property, frame):
        if frame.parent:
            return frame.parent.get_computed_property(property)
        else:
            if property in StyleNode._compute_functions:
                func = StyleNode._compute_functions[property]
                specified = _initial_values[property]
                result, _ = func(self, property, specified, frame)
            else:
                # Computed as specified
                result = _initial_values[property]
            return result

    def get_specified_differences(self, other):
        '''Return a set of specified properties (their names) that have
        different values in 'other' than 'self', or are only specified
        in one or the other.
        '''
        # Find all specified names that are unique to self or other.
        self_names = set()
        node = self
        while node:
            self_names |= set(node.specified_properties.keys())
            node = node.parent
        other_names = set()
        node = other
        while node:
            other_names |= set(node.specified_properties.keys())
            node = node.parent
        common_names = self_names & other_names
        differences = (self_names | other_names) - common_names

        # Find specified names that are common but have different values
        for property in common_names:
            # TODO optimisation avoid method call, inline
            if self.get_specified_property(property) != \
                other.get_specified_property(property):
                differences.add(property)
        return differences

    @css('font-size')
    def _compute_font_size(self, property, specified, frame):
        factor = None
        size = specified
        if type(size) == Dimension:
            if size.unit == 'em':
                factor = size
            elif size.unit == 'ex':
                factor = .5 * size
            else:
                size = self.render_device.dimension_to_pt(size)
        elif type(size) == Percentage:
            factor = size
        elif type(size) == Ident:
            if size == 'larger':
                factor = 1.1 # XXX wrong, should move to next size.
            elif size == 'smaller':
                factor = 0.9 # wrong again
            else:
                size = self.render_device.get_named_font_size(size)
        else:
            assert False

        if factor is not None:
            size = factor * self.get_inherited_property(property, frame)
            size = Dimension('%fpt' % size)
            return size, False
        return size, True

    @css('font-weight')
    def _compute_font_weight(self, property, specified, frame):
        if specified == 'normal':
            return 400, True
        elif specified == 'bold':
            return 700, True
        elif specified == 'bolder':
            rel = self.get_inherited_property(property, frame)
            return rel + 300, False
        elif specified == 'lighter':
            rel = self.get_inherited_property(property, frame)
            return rel - 300, False
        else:
            assert type(specified) in (Number, int, float)
            return specified, True

    @css('--font')
    def _compute_font(self, property, specified, frame):
        # It's *possible* this could be node-cacheable, but very unlikely
        # (the frame would have to have all font properties explicit,
        # none inherited).  Still worth caching on the frame though 
        # (remember that RenderDevice does its own font caching, so there
        # won't be duplicated objects).
        names = frame.get_computed_property('font-family')
        size = frame.get_computed_property('font-size')
        style = frame.get_computed_property('font-style')
        weight = frame.get_computed_property('font-weight')
        return self.render_device.get_font(names, size, style, weight), False

    @css('margin-top', 'margin-right', 'margin-bottom', 'margin-left',
         'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
         'width', 'min-width', 'max-width', 
         'height', 'min-height', 'max-height',
         )
    def _compute_font_relative_size(self, property, specified, frame):
        if type(specified) == Dimension:
            if specified.unit in ('em', 'ex'):
                font_size = frame.get_computed_property('font-size')
                result = self.render_device.dimension_to_device(
                    specified, font_size)
                return result, False
            else:
                result = self.render_device.dimension_to_device(
                    specified, 0)
                return result, True
        return specified, True

    @css('border-top-width', 'border-right-width', 'border-bottom-width',
         'border-left-width')
    def _compute_border_width(self, property, specified, frame):
        style = frame.get_computed_property(
            property.replace('width', 'style'))
        if style == 'none':
            return 0, False
        result, _ = self._compute_font_relative_size(
            property, specified, frame)
        return result, False

    @css('border-top-color', 'border-right-color', 'border-bottom-color',
         'border-left-color')
    def _compute_border_color(self, property, specified, frame):
        if specified is not None:
            return specified, True
        return frame.get_computed_property('color'), False

    @css('top', 'right', 'bottom', 'left')
    def _compute_position(self, property, specified, frame):
        position = frame.get_computed_property('position')
        if position == 'static':
            # Cache all of them now
            auto = Ident('auto')
            frame.computed_properties['top'] = auto
            frame.computed_properties['right'] = auto
            frame.computed_properties['bottom'] = auto
            frame.computed_properties['left'] = auto
            return auto, False
        elif position == 'relative':
            # Resolve relative positioning and cache
            # Careful not to recurse computing value, check specified first
            top = frame.style_context.get_specified_property('top')
            if top == 'inherit':
                top = self.get_inherited_property('top', frame)
            right = frame.style_context.get_specified_property('right')
            if right == 'inherit':
                right = self.get_inherited_property('right', frame)
            bottom = frame.style_context.get_specified_property('bottom')
            if bottom == 'inherit':
                bottom = self.get_inherited_property('bottom', frame)
            left = frame.style_context.get_specified_property('left')
            if left == 'inherit':
                left = self.get_inherited_property('left', frame)

            # Resolve under- and over-specified top/bottom
            if top == 'auto' and bottom == 'auto':
                top = bottom = 0
            elif top == 'auto':
                top = -bottom
            else:
                bottom = -top

            # Resolve under- and over-specified left/right
            if left == 'auto' and right == 'auto':
                left = right = 0
            elif left == 'auto':
                left = -right
            elif right == 'auto':
                right = -left
            elif frame.get_computed_value('direction') == 'rtl':
                left = -right
            else:
                right = -left

            # Convert to device units if possible
            if type(top) == Dimension:
                top = self.render_device.dimension_to_device(top)
            if type(right) == Dimension:
                right = self.render_device.dimension_to_device(right)
            if type(bottom) == Dimension:
                bottom = self.render_device.dimension_to_device(bottom)
            if type(left) == Dimension:
                left = self.render_device.dimension_to_device(left)

            # Cache at frame
            frame.computed_properties['top'] = top
            frame.computed_properties['right'] = right
            frame.computed_properties['bottom'] = bottom
            frame.computed_properties['left'] = left
            return frame.computed_properties[property], False
        else:
            raise NotImplementedError()
    
    @css('line-height')
    def _compute_line_height(self, property, specified, frame):
        if type(specified) == Dimension:
            return self._compute_font_relative_size(
                property, specified, frame)
        elif type(specified) in (Percentage, Number):
            size = frame.get_computed_property('font-size')
            size = self.render_device.dimension_to_device(size, size)
            return size * specified, False
        else:
            assert specified == 'normal'
            return specified, True
       
    def __repr__(self):
        return '<%s@0x%x %r>' % \
            (self.__class__.__name__, id(self), self.specified_properties)

StyleNode._compute_functions = _compute_functions
del _compute_functions


def validate_declaration(declaration):
    if declaration.property in _properties:
        attr, inheritable, multivalue, parse_func = \
            _properties[declaration.property]
        if not multivalue:
            if len(declaration.values) != 1:
                warnings.warn('CSS validation error in %s' % declaration.property)
                return ()
            value = declaration.values[0]
        else:
            value = declaration.values

        if (inheritable and 
            isinstance(value, Ident) and
            value == 'inherit'):
            if type(attr) in (list, tuple):
                return zip(attr, (value,) * len(attr))
            else:
                return ((attr, value))
        else:
            try:
                value = parse_func(value, None) # TODO no render_device
                if type(attr) in (list, tuple):
                    return zip(attr, value)
                else:
                    return ((attr, value),)
            except ValidationException:
                warnings.warn(
                    'CSS validation error in %s' % declaration.property)
                return ()
    else:
        warnings.warn('Unknown CSS property %s' % declaration.property)
        return ()


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
_parse_font_size = _parse_generic(Dimension, Percentage,
    'xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large',
    'larger', 'smaller')

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
    '--font',
]

_initial_values = {
    # 8 Box model
    # 8.3 Margin properties
    'margin-top': 0,
    'margin-bottom': 0,
    'margin-right': 0,
    'margin-left': 0,
    # 8.4 Padding properties
    'padding-top': 0,
    'padding-bottom': 0,
    'padding-right': 0,
    'padding-left': 0,
    # 8.5.1 Border width
    'border-top-width': 2,       # default to 'medium' if style != 'none'
    'border-right-width': 2,     # default to 'medium' if style != 'none'
    'border-bottom-width': 2,    # default to 'medium' if style != 'none'
    'border-left-width': 2,      # default to 'medium' if style != 'none'
    # 8.5.2 Border color
    'border-top-color': None,     # default to self.color
    'border-right-color': None,   # default to self.color
    'border-bottom-color': None,  # default to self.color
    'border-left-color': None,    # default to self.color
    # 8.5.3 Border style
    'border-top-style': Ident('none'),
    'border-right-style': Ident('none'),
    'border-bottom-style': Ident('none'),
    'border-left-style': Ident('none'),

    # 9 Visual formatting model
    # 9.2.4 The 'display' property
    # 'run-in' display must be resolved during box creation; the value
    # is not permitted in layout.
    'display': Ident('inline'),
    # 9.3.1 Choosing a positioning scheme: 'position' property
    'position': Ident('static'),
    # 9.3.2 Box offsets
    # Applies only to positioned elements (position != 'static')
    'top': Ident('auto'),
    'right': Ident('auto'),
    'bottom': Ident('auto'),
    'left': Ident('auto'),
    # 9.5.1 Positioning the float
    'float': Ident('none'),
    # 9.5.2 Controlling flow next to floats
    # Applies only to block-level elements
    'clear': Ident('none'),
    # 9.9.1 Specifying the stack level
    # Applies only to positioned elements
    'z-index': Ident('auto'),
    # 9.10 Text direction
    'direction': Ident('ltr'),
    'unicode-bidi': Ident('normal'),

    # 10 Visual formatting model details
    # 10.2 Content width
    'width': Ident('auto'),
    # 10.4 Minimum and maximum widths
    'min-width': 0,
    'max-width': Ident('none'),
    # 10.5 Content height
    'height': Ident('auto'),
    # 10.7 Minimum and maximum heights
    'min-height': 0,
    'max-height': Ident('none'),
    # 10.8 Line height calculations
    'line-height': Ident('normal'),

    # 11 Visual effects
    # 11.1.1 Overflow
    # Applies to non-replaced block-level elements, table cells and
    # inline-block elements
    'overflow': Ident('visible'),
    # 11.1.2 Clipping
    'clip': Ident('auto'),
    # 11.2 Visibility
    'visibility': Ident('visible'),
    # Applies to inline-level and 'table-cell' elements
    'vertical-align': Ident('baseline'),

    # 12 Generated content, automatic numbering, and lists
    # 12.2 The 'content' property
    # content, counters and quotes are not implemented here, performed
    # at box construction level.
    # 12.5.1 Lists
    # list-style-type is implemented at box construction level.
    'list-style-image': Ident('none'),
    # Applies to 'list-item' elements
    'list-style-position': Ident('outside'),

    # 13 Paged media
    # Page break properties are ignored by layout.

    # 14 Colors and Backgrounds
    # 14.1 Foreground color
    'color': Color.names['black'],    # Initial value is up to UA
    # 14.2.1 Background properties
    'background-color': Ident('transparent'),
    'background-image': Ident('none'),
    'background-repeat': Ident('repeat'),
    'background-attachment': Ident('scroll'),
    'background-position': (0, 0),

    # 15 Fonts
    # 15.3 Font family
    'font-family': (),
    # 15.4 Font styling
    'font-style': Ident('normal'),
    # 15.5 Small-caps
    'font-variant': Ident('normal'),
    # 15.6 Font boldness
    'font-weight': 400,
    # 15.7 Font size
    'font-size': Ident('medium'),

    # Internal property, gives actual Font object
    '--font': None,

    # 16 Text
    # 16.1 Indentation
    # Applies to block-level elements, table cells and inline blocks
    'text-indent': 0,
    # 16.2 Alignment
    # left if 'direction' is 'ltr', 'right' if 'direction is 'rtl'
    'text-align': None,
    # 16.3 Decoration
    'text-decoration': Ident('none'),
    # 16.4 Letter and word spacing
    'letter-spacing': Ident('normal'),
    'word-spacing': Ident('normal'),
    # 16.5 Capitalization
    'text-transform': Ident('none'),
    # 16.6 Whitespace
    # Steps 1-4 of 16.6.1 must be executed in formatter; layout engine only
    # performs steps beginning "As each line is laid out,".
    'white-space': Ident('normal'),

    # 17 Tables
    # 17.4.1 Caption position and alignment
    # Applies to table-caption elements
    'caption-side': Ident('top'),
    # 17.5.2 Table width algorithms
    'table-layout': Ident('auto'),
    # 17.6 Borders
    # Applies to 'table' and 'inline-table' elements
    'border-collapse': Ident('separate'),
    # Applies to 'table' and 'inline-table' elements
    'border-spacing': 0,
    # 17.6.1.1 Borders and Backgrounds around empty cells
    # Applies to 'table-cell' elements
    'empty-cells': Ident('show'),
}


