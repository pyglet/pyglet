#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.GL.VERSION_1_1 import *
from pyglet.scene2d.sprite import Sprite

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
        if not self._layout_width:
            for line in self.text.split('\n'):
                glyph_lines.append(self.font.get_glyphs(self.text))
        else:
            text = self.text + ' ' # Need the ' ' to always flush line.
            while text and text != ' ':
                line = self.font.get_glyphs_for_width(text, self._layout_width)
                text = text[len(line):]
                if text and text[0] == '\n':
                    text = text[1:]
                glyph_lines.append(line)

        # Create interleaved array and figure out state changes.
        line_height = self.font.ascent - self.font.descent + self.leading
        texture = None
        self._states = []
        state_from = 0
        state_length = 0
        y = 0
        lst = []
        self._text_width = 0
        for glyphs in glyph_lines:
            x = 0
            for i, glyph in enumerate(glyphs):
                if glyph.texture != texture:
                    if state_length:
                        self._states.append((state_from, state_length, texture))
                    texture = glyph.texture
                    state_from = i
                    state_length = 0
                state_length += 1

                lst += [glyph.tex_coords[0], glyph.tex_coords[1],
                        x + glyph.vertices[0], y + glyph.vertices[1], 0.,
                        glyph.tex_coords[2], glyph.tex_coords[1],
                        x + glyph.vertices[2], y + glyph.vertices[1], 0.,
                        glyph.tex_coords[2], glyph.tex_coords[3],
                        x + glyph.vertices[2], y + glyph.vertices[3], 0.,
                        glyph.tex_coords[0], glyph.tex_coords[3],
                        x + glyph.vertices[0], y + glyph.vertices[3], 0.]
                x += glyph.advance
            self._text_width = max(self._text_width, x)
            y -= line_height

        self._text_height = -y
        self._array = (c_float * len(lst))(*lst)
        self._states.append((state_from, state_length, texture))        

        self._dirty = False
        
    def draw(self):
        if self._dirty:
            self._clean()

        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)

        # XXX Safe to assume all required textures will use same blend state I
        # think.  (otherwise move this into loop)
        self._states[0][2].apply_blend_state()

        glColor4f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        glInterleavedArrays(GL_T2F_V3F, 0, self._array)
        for state_from, state_length, texture in self._states:
            glBindTexture(GL_TEXTURE_2D, texture.id)
            glDrawArrays(GL_QUADS, state_from * 4, state_length * 4)
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

    def del_width(self):
        del self._layout_width
        self._dirty = True

    width = property(get_width, set_width, del_width)

    def get_height(self):
        if self._dirty:
            self._clean()
        return self._text_height

    height = property(get_height)

    def set_text(self, text):
        self._text = text
        self._dirty = True

    text = property(lambda self: self._text, set_text)
