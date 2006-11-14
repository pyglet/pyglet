#!/usr/bin/env python

'''
Pseudo-HTML parser for creating attributed character runs.

This is by no means an HTML parser, but is based loosely on HTML4
character markup.  The parser is based on HTMLParser, so it does
not need to be well-formed or valid.  Unrecognised tags and
attributes will be ignored.  All tags are case-insensitive.  The following
tags are recognised:

    ``<b>`` or ``<strong>``
        Bold style.  For example::

            This is <b>bold</b>.

    ``<i>`` or ``<em>``
        Italic style.  For example::

            This is <i>italic</i>.
    ``<small>`` and ``<big>``
        Reduces or increases font size by 2pt.  For example::

            This is <small>small text</small>.

    ``<font face=".." size=".." color="..">``
        Changes the font.  All attributes are optional; if unspecified,
        the inherited value will be unchanged.

            face
                Name of the font family.  For example, ``'times new roman'``.
            size
                Size of the font, in points.  For example, ``12``.
            color
                Color of the font, either one of the standard color names:
                    * black
                    * silver
                    * gray
                    * white
                    * maroon
                    * red
                    * purple
                    * fuchsia
                    * gree
                    * lime
                    * olive
                    * yellow
                    * navy
                    * blue
                    * teal
                    * aqua
                or as a hexadecimal RGB triplet or RGBA quad.  For example,
                ``#00ff00`` is bright green, and ``#ff000080`` is translucent
                bright red.
            For example::
                
                <font face="helvetica" size="16" color="red">Boo!</font>

    ``<p align="..">`` or ``<div align="..">``
        Begin a new paragraph.  ``align`` is optional and can be one of:
            * left
            * right
            * center
        If not specified, it will be inherited.  Paragraphs can be specified
        as stand-alone ``<p>`` tags between text, or in the more modern
        bracketing fashion::

            <p>A new paragraph.</p>
    ``<br>``
        A line break.
           
The typical way to use this module is to call `parse` with some text
and a `pyglet.text.font.LocalFontFactory`, and pass the result to
`pyglet.text.layout.OpenGLTextLayout` for rendering.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import HTMLParser
import re

from pyglet.text import layout

class Attribute:
    Bold = 1
    Italic = 2
    FontSize = 3
    FontName = 4
    Color = 5

class ParagraphAttribute:
    Justification = 1

ParagraphAlignments = {
    'left': layout.Align.left,
    'center': layout.Align.center,
    'right': layout.Align.right
}

ColorNames = {
    'black': (0, 0, 0, 1),
    'silver': (0.75, 0.75, 0.75, 1),
    'gray': (0.5, 0.5, 0.5, 1),
    'white': (1, 1, 1, 1),
    'maroon': (0.5, 0, 0, 1),
    'red': (1, 0, 0, 1),
    'purple': (0.5, 0, 0.5, 1),
    'fuchsia': (1, 0, 1, 1),
    'green': (0, 0.5, 0, 1),
    'lime': (0, 1, 0, 1),
    'olive': (0.5, 0.5, 0, 1),
    'yellow': (1, 1, 0, 1),
    'navy': (0, 0, 0.5, 1),
    'blue': (0, 0, 1, 1),
    'teal': (0, 0.5, 0.5, 1),
    'aqua': (0, 1, 1, 1),
}

class StylePrototype:
    def __init__(self, font_factory, inherit=None):
        self.font_factory = font_factory
        self._attrs = {}
        self._style = None
        if inherit:
            for attr, value in inherit._attrs.items():
                self._attrs[attr] = value
        else:
            # Default attributes for empty style
            self._attrs[Attribute.Bold] = False
            self._attrs[Attribute.Italic] = False
            self._attrs[Attribute.FontSize] = 12
            self._attrs[Attribute.FontName] = 'bitstream vera sans'
            self._attrs[Attribute.Color] = (0, 0, 0, 1)
    
    def set_attribute(self, attribute, value):
        self._attrs[attribute] = value
        return self

    def get_style(self):
        if not self._style:
            bold = self._attrs[Attribute.Bold]
            italic = self._attrs[Attribute.Italic]
            size = self._attrs[Attribute.FontSize]
            fontname = self._attrs[Attribute.FontName]
            font = self.font_factory.get_font(fontname,
                size=size, bold=bold, italic=italic)
            self._style = layout.Style(font, self._attrs[Attribute.Color])
        return self._style

    def __repr__(self):
        return 'StylePrototype(%s)' % self._attrs

class ParagraphPrototype:
    def __init__(self, inherit=None):
        self._attrs = {}
        if inherit:
            for attr, value in inherit._attrs.items():
                self._attrs[attr] = value
        else:
            # Default attributes
            self._attrs[ParagraphAttribute.Justification] = layout.Align.left

    def set_attribute(self, attribute, value):
        self._attrs[attribute] = value
        return self

    def create_paragraph(self, style):
        marker = self.create_break(style)
        return marker

    def create_break(self, style):
        justification = self._attrs[ParagraphAttribute.Justification]
        return layout.ParagraphMarker(style,
            justification=justification)

class Parser(HTMLParser.HTMLParser):
    whitespace_pattern = re.compile('[ \t\r\n]+')

    def __init__(self, font_factory):
        HTMLParser.HTMLParser.__init__(self)
        self.runs = []
        self.paragraph_stack = [(None, ParagraphPrototype())]
        self.style_stack = [(None, StylePrototype(font_factory))]
        self.font_factory = font_factory
        self.have_paragraph = False
        self.have_whitespace = True

    def push_style(self, tag):
        style = StylePrototype(self.font_factory, self.style_stack[-1][1])
        self.style_stack.append((tag, style))
        return style

    def peek_style(self):
        return self.style_stack[-1][1].get_style()

    def push_paragraph(self, tag):
        paragraph = ParagraphPrototype(self.paragraph_stack[-1][1])
        self.paragraph_stack.append((tag, paragraph))
        return paragraph

    def peek_paragraph(self):
        return self.paragraph_stack[-1][1]

    def parse_color(self, value):
        value = value.lower()
        if value in ColorNames:
            return ColorNames[value]
        elif value and value[0] == '#':
            num = int(value[1:], 16)
            alpha = 1.0
            if len(value) == 9:
                # alpha specified
                alpha = (num & 0xff) / 256.0
                num >>= 8
            b = (num & 0xff) / 256.0
            g = ((num>>8) & 0xff) / 256.0
            r = ((num>>16) & 0xff) / 256.0
            return (r, g, b, alpha)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        old_attrs = self.style_stack[-1][1]._attrs
        if tag == 'b' or tag == 'strong':
            self.push_style(tag).set_attribute(Attribute.Bold, True)
        elif tag == 'i' or tag == 'em':
            self.push_style(tag).set_attribute(Attribute.Italic, True)
        elif tag == 'big':
            size = old_attrs[Attribute.FontSize] + 2
            self.push_style(tag).set_attribute(Attribute.FontSize, size)
        elif tag == 'small':
            size = old_attrs[Attribute.FontSize] - 2
            self.push_style(tag).set_attribute(Attribute.FontSize, size)
        elif tag == 'font':
            style = self.push_style(tag)
            for key, value in attrs:
                if key == 'size':
                    # Differing from HTML4: size is in points, not 1-7 scale.
                    style.set_attribute(Attribute.FontSize, int(value))
                elif key == 'color':
                    color = self.parse_color(value)
                    style.set_attribute(Attribute.Color, color)
                elif key == 'face':
                    style.set_attribute(Attribute.FontName, value)
        elif tag == 'p' or tag == 'div':
            self.have_paragraph = True
            para = self.push_paragraph(tag)
            for key, value in attrs:
                if key == 'align' and value in ParagraphAlignments:
                    para.set_attribute(ParagraphAttribute.Justification,
                                      ParagraphAlignments[value])
            self.runs.append(para.create_paragraph(self.peek_style()))
        elif tag == 'br':
            self.runs.append(self.peek_paragraph().create_break(self.peek_style()))

    def handle_endtag(self, tag):
        tag = tag.lower()
        # Find highest matching tag on stack -- very tolerant of mismatched
        # tags
        if tag in ('p', 'div'):
            stack = self.paragraph_stack
            self.have_paragraph = False
        else:
            stack = self.style_stack
        for i in range(len(stack) - 1, -1, -1):
            if stack[i][0] == tag:
                del stack[i:]
                return
        # Ignore non-matching end tag

    def handle_data(self, data):
        output = self.whitespace_pattern.sub(' ', data.strip())
        if not self.have_whitespace and data[0] in ' \r\t\n':
            output = ' ' + output
        if data[-1] in ' \r\t\n':
            self.have_whitespace = True
            output = output + ' '
        if not output:
            return
        if not self.have_paragraph:
            self.runs.append(
                self.peek_paragraph().create_paragraph(self.peek_style()))
            self.have_paragraph = True
        self.runs.append(layout.StyledRun(output, self.peek_style()))

    def handle_charref(self, name):
        pass

    def handle_entityref(self, name):
        pass
    

def parse(input, font_factory):
    """Parse an HTML document fragment and return a list of 
    `pyglet.text.layout.StyledRun`.
    
    :Parameters:
        `input` : str
            HTML marked-up text.  See the module docstring for specific
            tag information.
        `font_factory` : pyglet.text.font.FontFactory
            FontFactory to use for locating and instantiating fonts.
    """
    parser = Parser(font_factory)
    parser.feed(input)
    parser.close()
    return parser.runs
