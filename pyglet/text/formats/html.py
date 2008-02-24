#!/usr/bin/env python

'''Decode HTML into attributed text.

A subset of HTML 4.01 Transitional is implemented.  The following elements are
supported fully::

    B BLOCKQUOTE BR CENTER CODE DD DIR DL EM FONT H1 H2 H3 H4 H5 H6 I IMG KBD
    LI MENU OL P PRE Q SAMP STRONG SUB SUP TT U UL VAR 

The mark (bullet or number) of a list item is separated from the body of the
list item with a tab, as the pyglet document model does not allow
out-of-stream text.  This means lists display as expected, but behave a little
oddly if edited.

No CSS styling is supported.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import HTMLParser
import htmlentitydefs
import os
import re

import pyglet
from pyglet.text.formats import structured

def int_to_roman(input):
    # From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/81611
    if not 0 < input < 4000:
        raise ValueError, "Argument must be between 1 and 3999"    
    ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,   4,  1)
    nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
    result = ""
    for i in range(len(ints)):
        count = int(input / ints[i])
        result += nums[i] * count
        input -= ints[i] * count
    return result

def _hex_color(val):
    return [(val >> 16) & 0xff, (val >> 8) & 0xff, val & 0xff, 255]

_font_sizes = {
    1: 8,
    2: 10,
    3: 12,
    4: 14,
    5: 18,
    6: 24,
    7: 48
}

_color_names = {
    'black':    _hex_color(0x000000),
    'silver':   _hex_color(0xc0c0c0),
    'gray':     _hex_color(0x808080),
    'white':    _hex_color(0xffffff),
    'maroon':   _hex_color(0x800000),
    'red':      _hex_color(0xff0000),
    'purple':   _hex_color(0x800080),
    'fucsia':   _hex_color(0x008000),
    'green':    _hex_color(0x00ff00),
    'lime':     _hex_color(0xffff00),
    'olive':    _hex_color(0x808000),
    'yellow':   _hex_color(0xff0000),
    'navy':     _hex_color(0x000080),
    'blue':     _hex_color(0x0000ff),
    'teal':     _hex_color(0x008080),
    'aqua':     _hex_color(0x00ffff),
}

def _parse_color(value):
    if value.startswith('#'):
        return _hex_color(int(value[1:], 16))
    else:
        try:
            return _color_names[value.lower()]
        except KeyError:
            raise ValueError()

_whitespace_re = re.compile(u'[\u0020\u0009\u000c\u200b\r\n]+', re.DOTALL)

_metadata_elements = ['head', 'title']

_block_elements = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                   'ul', 'ol', 'dir', 'menu', 
                   'pre', 'dl', 'div', 'center', 
                   'noscript', 'noframes', 'blockquote', 'form',
                   'isindex', 'hr', 'table', 'fieldset', 'address',
                    # Incorrect, but we treat list items as blocks:
                   'li', 'dd', 'dt', ]
                  

_block_containers = ['_top_block', 
                     'body', 'div', 'center', 'object', 'applet',
                     'blockquote', 'ins', 'del', 'dd', 'li', 'form',
                     'fieldset', 'button', 'th', 'td', 'iframe', 'noscript',
                     'noframes',
                     # Incorrect, but we treat list items as blocks:
                     'ul', 'ol', 'dir', 'menu', 'dl']

class ImageElement(pyglet.text.document.InlineElement):
    def __init__(self, image, width=None, height=None):
        self.image = image.get_texture()
        self.width = width is None and image.width or width
        self.height = height is None and image.height or height
        self.vertex_lists = {}

        anchor_y = self.height / image.height * image.anchor_y
        ascent = max(0, self.height - anchor_y)
        descent = min(0, -anchor_y)
        super(ImageElement, self).__init__(ascent, descent, self.width)

    def place(self, layout, x, y):
        group = pyglet.graphics.TextureGroup(self.image.texture, 
                                             layout.top_group)
        x1 = x
        y1 = y + self.descent
        x2 = x + self.width
        y2 = y + self.height + self.descent
        vertex_list = layout.batch.add(4, pyglet.gl.GL_QUADS, group,
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
            ('t3f', self.image.tex_coords))
        self.vertex_lists[layout] = vertex_list

    def remove(self, layout):
        self.vertex_lists[layout].delete()
        del self.vertex_lists[layout]

class UnorderedList(object):
    def __init__(self, attrs):
        type = attrs.get('type', 'disc').lower()
        if type == 'circle':
            self.mark = u'\u25cb'
        elif type == 'square':
            self.mark = u'\u25a1'
        else:
            self.mark = u'\u25cf'

    def get_mark(self, attrs):
        return self.mark

class OrderedList(object):
    def __init__(self, attrs):
        try:
            self.next_value = int(attrs['start'])
        except (KeyError, ValueError):
            self.next_value = 1
        self.type = attrs.get('type', '1')

    def get_mark(self, attrs):
        try:
            value = int(attrs['value'])
        except (KeyError, ValueError):
            value = self.next_value
        self.next_value = value + 1
        if self.type in 'aA':
            try:
                mark = 'abcdefghijklmnopqrstuvwxyz'[value - 1]
            except ValueError:
                mark = '?'
            if self.type == 'A':
                mark = mark.upper()
            return '%s.' % mark
        elif self.type in 'iI':
            try:
                mark = int_to_roman(value)
            except ValueError:
                mark = '?'
            if self.type == 'i':
                mark = mark.lower()
            return mark
        else:
            return '%d.' % value

class HTMLDecoder(HTMLParser.HTMLParser, structured.StructuredTextDecoder):
    def decode_structured(self, text, path):
        self.path = path
        self._font_size_stack = [3]
        self.list_stack = [UnorderedList({})]
        self.strip_leading_space = True
        self.block_begin = True
        self.need_block_begin = False
        self.element_stack = ['_top_block']
        self.in_metadata = False
        self.in_pre = False

        self.push_style('_default', {
            'font_name': 'Times New Roman',
            'font_size': 12,
            'margin_bottom': 12,
        })

        self.feed(text)
        self.close()

    def get_image(self, filename):
        filename = os.path.join(self.path, filename)
        return pyglet.image.load(filename)

    def prepare_for_data(self):
        if self.need_block_begin:
            self.add_text('\n')
            self.block_begin = True
            self.need_block_begin = False

    def handle_data(self, data):
        if self.in_metadata:
            return

        if self.in_pre:
            self.add_text(data)
        else:
            data = _whitespace_re.sub(' ', data)
            if data.strip():
                self.prepare_for_data()
                if self.block_begin or self.strip_leading_space:
                    data = data.lstrip()
                    self.block_begin = False
                self.add_text(data)
            self.strip_leading_space = data.endswith(' ')

    def handle_starttag(self, tag, case_attrs):
        if self.in_metadata:
            return

        element = tag.lower()
        attrs = {}
        for key, value in case_attrs:
            attrs[key.lower()] = value

        if element in _metadata_elements:
            self.in_metadata = True
        elif element in _block_elements:
            # Pop off elements until we get to a block container.
            while self.element_stack[-1] not in _block_containers:
                self.handle_endtag(self.element_stack[-1])
            if not self.block_begin:
                self.add_text('\n')
                self.block_begin = True
                self.need_block_begin = False
        self.element_stack.append(element)

        style = {}
        if element in ('b', 'strong'):
            style['bold'] = True
        elif element in ('i', 'em', 'var'):
            style['italic'] = True
        elif element in ('tt', 'code', 'samp', 'kbd'):
            style['font_name'] = 'Courier New'
        elif element == 'u':
            color = self.current_style.get('color')
            if color is None: 
                color = [0, 0, 0, 255]
            style['underline'] = color
        elif element == 'font':
            if 'face' in attrs:
                style['font_name'] = attrs['face'].split(',')
            if 'size' in attrs:
                size = attrs['size']
                try:
                    if size.startswith('+'):
                        size = self._font_size_stack[-1] + int(size[1:])
                    elif size.startswith('-'):
                        size = self._font_size_stack[-1] - int(size[1:])
                    else:
                        size = int(size)
                except ValueError:
                    size = 3
                self._font_size_stack.append(size)
                if size in _font_sizes:
                    style['font_size'] = _font_sizes.get(size, 3)
            else:
                self._font_size_stack.append(self._font_size_stack[-1])
            if 'color' in attrs:
                try:
                    style['color'] = _parse_color(attrs['color'])
                except ValueError:
                    pass
        elif element == 'sup':
            size = self._font_size_stack[-1] - 1
            style['font_size'] = _font_sizes.get(size, 1)
            style['baseline'] = 3
        elif element == 'sub':
            size = self._font_size_stack[-1] - 1
            style['font_size'] = _font_sizes.get(size, 1)
            style['baseline'] = -3
        elif element == 'h1':
            style['font_size'] = 24
            style['bold'] = True
            style['align'] = 'center'
        elif element == 'h2':
            style['font_size'] = 18
            style['bold'] = True
        elif element == 'h3':
            style['font_size'] = 16
            style['bold'] = True
        elif element == 'h4':
            style['font_size'] = 14
            style['bold'] = True
        elif element == 'h5':
            style['font_size'] = 12
            style['bold'] = True
        elif element == 'h6':
            style['font_size'] = 12
            style['italic'] = True
        elif element == 'br':
            self.add_text(u'\u2028')
            self.strip_leading_space = True
        elif element == 'p':
            if attrs.get('align') in ('left', 'center', 'right'):
                style['align'] = attrs['align']
        elif element == 'center':
            style['align'] = 'center'
        elif element == 'pre':
            style['font_name'] = 'Courier New'
            style['margin_bottom'] = 0
            self.in_pre = True
        elif element == 'blockquote':
            left_margin = self.current_style.get('margin_left') or 0
            right_margin = self.current_style.get('margin_right') or 0
            style['margin_left'] = left_margin + 60
            style['margin_right'] = right_margin + 60
        elif element == 'q':
            self.handle_data(u'\u201c')
        elif element in ('ul', 'ol', 'dir', 'menu'):
            left_margin = self.current_style.get('margin_left') or 0
            tab_stops = self.current_style.get('tab_stops')
            if tab_stops:
                tab_stops = list(tab_stops)
            else:
                tab_stops = []
            tab_stops.append(left_margin + 50)
            style['margin_left'] = left_margin + 50
            style['indent'] = -30
            style['tab_stops'] = tab_stops
            if element == 'ol':
                self.list_stack.append(OrderedList(attrs))
            else:
                self.list_stack.append(UnorderedList(attrs))
        elif element == 'li':
            self.handle_data(self.list_stack[-1].get_mark(attrs))
            self.add_text('\t')
            self.strip_leading_space = True
        elif element == 'dl':
            style['margin_bottom'] = 0
        elif element == 'dd':
            left_margin = self.current_style.get('margin_left') or 0
            style['margin_left'] = left_margin + 30
        elif element == 'img':
            image = self.get_image(attrs.get('src'))
            if image:
                width = attrs.get('width')
                if width:
                    width = int(width)
                height = attrs.get('height')
                if height:
                    height = int(height)
                self.prepare_for_data()
                self.add_element(ImageElement(image, width, height))
                self.strip_leading_space = False

        self.push_style(element, style)

    def handle_endtag(self, tag):
        element = tag.lower()
        if element not in self.element_stack:
            return

        self.pop_style(element)
        while self.element_stack.pop() != element:
            pass

        if element in _metadata_elements:
            self.in_metadata = False
        elif element in _block_elements:
            self.block_begin = False
            self.need_block_begin = True

        if element == 'font' and len(self._font_size_stack) > 1:
            self._font_size_stack.pop()
        elif element == 'pre':
            self.in_pre = False
        elif element == 'q':
            self.handle_data(u'\u201d')
        elif element in ('ul', 'ol'):
            if len(self.list_stack) > 1:
                self.list_stack.pop()

    def handle_entityref(self, name):
        if name in htmlentitydefs.name2codepoint:
            self.handle_data(unichr(htmlentitydefs.name2codepoint[name]))
    
    def handle_charref(self, name):
        name = name.lower()
        try:
            if name.startswith('x'):
                self.handle_data(unichr(int(name[1:], 16)))
            else:
                self.handle_data(unichr(int(name)))
        except ValueError:
            pass
