#!/usr/bin/env python

'''Load fonts and render text.

This is a fairly-low level interface to text rendering.  Obtain a font using
`load`::

    from pyglet import font
    arial = font.load('Arial', 14, bold=True, italic=False)

pyglet will load any system-installed fonts.  You can add additional fonts
(for example, from your program resources) using `add_file` or
`add_directory`.

Obtain a list of `Glyph` objects for a string of text using the `Font`
object::

    text = 'Hello, world!'
    glyphs = arial.get_glyphs(text)

The most efficient way to render these glyphs is with a `GlyphString`::

    glyph_string = GlyphString(text, glyphs)
    glyph_string.draw()

There are also a variety of methods in both `Font` and `GlyphString` to
facilitate word-wrapping.

For complex multi-font rendering and layout, consider the `pyglet.ext.layout`
package.

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import os
import math

from pyglet.gl import *
from pyglet import window
from pyglet import image

class GlyphString(object):
    '''An immutable string of glyphs that can be rendered quickly.

    This class is ideal for quickly rendering single or multi-line strings
    of text that use the same font.  To wrap text using a glyph string,
    call `get_break_index` to find the optimal breakpoint for each line,
    the repeatedly call `draw` for each breakpoint.
    '''

    def __init__(self, text, glyphs, x=0, y=0):
        '''Create a glyph string.
        
        The `text` string is used to determine valid breakpoints; all glyphs
        must have already been determined using `Font.get_glyphs`.  The string
        will be positioned with the baseline of the left-most glyph at the
        given coordinates.
        
        :Parameters:
            `text` : str or unicode
                String to represent.
            `glyphs` : list of `pyglet.font.base.Glyph`
                Glyphs representing `text`.
            `x` : float
                X coordinate of the left-side bearing of the left-most glyph.
            `y` : float
                Y coordinate of the baseline.

        '''
        # Create an interleaved array in GL_T2F_V3F format and determine
        # state changes required.
        
        lst = []
        texture = None
        self.text = text
        self.states = []
        self.cumulative_advance = [] # for fast post-string breaking
        state_from = 0
        state_length = 0
        for i, glyph in enumerate(glyphs):
            if glyph.owner != texture:
                if state_length:
                    self.states.append((state_from, state_length, texture))
                texture = glyph.owner
                state_from = i
                state_length = 0
            state_length += 1
            lst += [glyph.tex_coords[0][0], glyph.tex_coords[0][1],
                    x + glyph.vertices[0], y + glyph.vertices[1], 0.,
                    glyph.tex_coords[1][0], glyph.tex_coords[1][1],
                    x + glyph.vertices[2], y + glyph.vertices[1], 0.,
                    glyph.tex_coords[2][0], glyph.tex_coords[2][1],
                    x + glyph.vertices[2], y + glyph.vertices[3], 0.,
                    glyph.tex_coords[3][0], glyph.tex_coords[3][1],
                    x + glyph.vertices[0], y + glyph.vertices[3], 0.]
            x += glyph.advance
            self.cumulative_advance.append(x)
        self.states.append((state_from, state_length, texture))

        self.array = (c_float * len(lst))(*lst)
        self.width = x

    def get_break_index(self, from_index, width):
        '''Find a breakpoint within the text for a given width.
        
        Returns a valid breakpoint after `from_index` so that the text
        between `from_index` and the breakpoint fits within `width` pixels.

        This method uses precomputed cumulative glyph widths to give quick
        answer, and so is much faster than 
        `pyglet.font.base.Font.get_glyphs_for_width`.  

        :Parameters:
            `from_index` : int
                Index of text to begin at, or 0 for the beginning of the
                string. 
            `width` : float
                Maximum width to use.

        :rtype: int
        :return: the index of text which will be used as the breakpoint, or
            `from_index` if there is no valid breakpoint.
        '''
        to_index = from_index
        if from_index >= len(self.text):
            return from_index
        if from_index:
            width += self.cumulative_advance[from_index-1]
        for i, (c, w) in enumerate(
                zip(self.text[from_index:], 
                    self.cumulative_advance[from_index:])):
            if w > width:
                return to_index 
            if c == '\n':
                return i + from_index + 1
            elif c in u'\u0020\u200b':
                to_index = i + from_index + 1
        return to_index

    def get_subwidth(self, from_index, to_index):
        '''Return the width of a slice of this string.

        :Parameters:
            `from_index` : int
                The start index of the string to measure.
            `to_index` : int
                The end index (exclusive) of the string to measure.

        :rtype: float
        '''
        width = self.cumulative_advance[to_index-1] 
        if from_index:
            width -= self.cumulative_advance[from_index-1]
        return width

    def draw(self, from_index=0, to_index=None):
        '''Draw a region of the glyph string.
        
        Assumes texture state is enabled.  To enable the texture state::

            from pyglet.gl import *
            glEnable(GL_TEXTURE_2D)

        :Parameters:
            `from_index` : int
                Start index of text to render.
            `to_index` : int
                End index (exclusive) of text to render.

        '''
        if from_index >= len(self.text) or \
           from_index == to_index or \
           not self.text:
            return

        # XXX Safe to assume all required textures will use same blend state I
        # think.  (otherwise move this into loop)
        self.states[0][2].apply_blend_state()

        if from_index:
            glPushMatrix()
            glTranslatef(-self.cumulative_advance[from_index-1], 0, 0)
        if to_index is None:
            to_index = len(self.text)

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glInterleavedArrays(GL_T2F_V3F, 0, self.array)
        for state_from, state_length, texture in self.states:
            if state_from + state_length < from_index:
                continue
            state_from = max(state_from, from_index)
            state_length = min(state_length, to_index - state_from)
            if state_length <= 0:
                break
            glBindTexture(GL_TEXTURE_2D, texture.id)
            glDrawArrays(GL_QUADS, state_from * 4, state_length * 4)
        glPopClientAttrib()

        if from_index:
            glPopMatrix()

class Label(object):
    '''Simple displayable text.
    '''

    _layout_width = None  # Width to layout text to
    _text_width = 0       # Calculated width of text
    _text_height = 0      # Calculated height of text (bottom descender to top
                          # ascender)

    _dirty = False        # Flag if require layout

    # Alignment constants
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'
    BOTTOM = 'bottom'
    BASELINE = 'baseline'
    TOP = 'top'

    halign = LEFT
    valign = BASELINE

    def __init__(self, font, text='', x=0, y=0, z=0, color=(1,1,1,1)):
        self._dirty = True
        self.font = font
        self._text = text
        self.color = color
        self.x = x
        self.y = y
        self.leading = 0

    def _clean(self):
        '''Resolve changed layout'''
        text = self._text + ' '
        glyphs = self.font.get_glyphs(text)
        self._glyph_string = GlyphString(text, glyphs)

        self.lines = []
        i = 0
        if self._layout_width is None:
            self._text_width = 0
            while '\n' in text[i:]:
                end = text.index('\n', i)
                self.lines.append((i, end))
                self._text_width = max(self._text_width, 
                                       self._glyph_string.get_subwidth(i, end))
                i = end + 1
            end = len(text)
            if end != i:
                self.lines.append((i, end))
                self._text_width = max(self._text_width,
                                       self._glyph_string.get_subwidth(i, end))
                                   
        else:
            bp = self._glyph_string.get_break_index(i, self._layout_width)
            while i < len(text) and bp > i:
                if text[bp-1] == '\n':
                    self.lines.append((i, bp - 1))
                else:
                    self.lines.append((i, bp))
                i = bp
                bp = self._glyph_string.get_break_index(i, self._layout_width)
            if i < len(text) - 1:
                self.lines.append((i, len(text)))
            
        self.line_height = self.font.ascent - self.font.descent + self.leading
        self._text_height = self.line_height * len(self.lines)

        self._dirty = False
        
    def draw(self):
        if self._dirty:
            self._clean()

        x = self.x
        if self.halign == self.RIGHT:
            raise NotImplementedError('no align yet')
            x += self._layout_width - self.width
        elif self.halign == self.CENTER:
            raise NotImplementedError('no align yet')
            x += -self._layout_width / 2 + self._text_width / 2

        y = self.y
        if self.valign == self.BOTTOM:
            y += self.height
        elif self.valign == self.CENTER:
            y += self.height / 2
        elif self.valign == self.TOP:
            y -= self.font.ascent

        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glColor4f(*self.color)
        glPushMatrix()
        glTranslatef(x, y, 0)
        for start, end in self.lines:
            self._glyph_string.draw(start, end)
            glTranslatef(0, -self.line_height, 0)
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


# Load platform dependent module
if sys.platform == 'darwin':
    from pyglet.font.carbon import CarbonFont
    _font_class = CarbonFont
elif sys.platform == 'win32':
    from pyglet.font.win32 import Win32Font
    _font_class = Win32Font
else:
    from pyglet.font.freetype import FreeTypeFont
    _font_class = FreeTypeFont

def load(name, size, bold=False, italic=False):
    '''Load a font for rendering.

    :Parameters:
        `name` : str, or list of str
            Font family, for example, "Times New Roman".  If a list of names
            is provided, the first one matching a known font is used.  If no
            font can be matched to the name(s), a default font is used.
        `size` : float
            Size of the font, in points.  The returned font may be an exact
            match or the closest available.
        `bold` : bool
            If True, a bold variant is returned, if one exists for the given
            family and size.
        `italic` : bool
            If True, an italic variant is returned, if one exists for the given
            family and size.

    :rtype: `pyglet.font.base.Font`
    '''
    # Find first matching name
    if type(name) in (tuple, list):
        for n in name:
            if _font_class.have_font(n):
                name = n
                break
        else:
            name = None

    # Locate or create font cache   
    shared_object_space = window.get_current_context().get_shared_object_space()
    if not hasattr(shared_object_space, 'pyglet_font_font_cache'):
        shared_object_space.pyglet_font_font_cache = {}
    font_cache = shared_object_space.pyglet_font_font_cache

    # Look for font name in font cache
    descriptor = (name, size, bold, italic)
    if descriptor in font_cache:
        return font_cache[descriptor]

    # Not in cache, create from scratch
    font = _font_class(name, size, bold=bold, italic=italic)
    font_cache[descriptor] = font
    return font

def add_file(font):
    if type(font) in (str, unicode):
        font = open(font, 'rb')
    if hasattr(font, 'read'):
        font = font.read()
    _font_class.add_font_data(font)


def add_directory(dir):
    import os
    for file in os.listdir(dir):
        if file[:-4].lower() == '.ttf':
            add_file(file)

