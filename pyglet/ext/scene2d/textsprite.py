#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.gl import *
from pyglet.ext.scene2d.sprite import Sprite
from pyglet.font import GlyphString

# TODO: inherit from Sprite
class TextSprite(object):
    _layout_width = None  # Width to layout text to
    _text_width = 0       # Calculated width of text
    _text_height = 0      # Calculated height of text (bottom descender to top
                          # ascender)

    _dirty = False        # Flag if require layout
    _states = None        # List of state changes when drawing
    _array = None         # Interleaved vertex/texcoord array

    def __init__(self, font, text, x=0, y=0, z=0, color=(1,1,1,1)):
        self._dirty = True
        self.font = font
        self._text = text
        self.color = color
        self.x = x
        self.y = y
        self.leading = 0

    def _clean(self):
        '''Resolve changed layout'''

        # Each 'line' in 'glyph_lines' is a list of Glyph objects.  Do
        # line wrapping now.
        glyph_lines = []
        if self._layout_width is None:
            for line in self.text.split('\n'):
                glyph_lines.append((line, self.font.get_glyphs(self.text)))
        else:
            text = self.text + ' ' # Need the ' ' to always flush line.
            while text and text != ' ':
                line = self.font.get_glyphs_for_width(text, self._layout_width)
                glyph_lines.append((text[:len(line)], line))
                text = text[len(line):]
                if text and text[0] == '\n':
                    text = text[1:]

        # Create interleaved array and figure out state changes.
        line_height = self.font.ascent - self.font.descent + self.leading
        y = 0
        self._text_width = 0
        self.strings = []
        for text, glyphs in glyph_lines:
            string = GlyphString(text, glyphs, 0, y)
            self._text_width = max(self._text_width, string.width)
            y -= line_height
            self.strings.append(string)

        self._text_height = -y

        self._dirty = False
        
    def draw(self):
        if self._dirty:
            self._clean()

        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glColor4f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        for string in self.strings:
            string.draw()
        glPopMatrix()
        glPopAttrib()

    def get_width(self):
        if self._dirty:
            self._clean()
        if self._layout_width:
            return self._layout_width
        return self._text_width

    def set_width(self, width):
        self._layout_width = width
        self._dirty = True

    width = property(get_width, set_width)

    def get_height(self):
        if self._dirty:
            self._clean()
        return self._text_height

    height = property(get_height)

    def set_text(self, text):
        self._text = text
        self._dirty = True

    text = property(lambda self: self._text, set_text)


