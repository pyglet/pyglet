#!/usr/bin/env python

'''

No bidi support needs to be in from the start, but keep in mind it will 
be eventually, so don't make it too left-to-rightist.

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import os

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *

class Glyph(TextureSubImage):
    advance = 0
    vertices = (0, 0, 0, 0)

    def set_bearings(self, baseline, left_side_bearing, advance):
        self.advance = advance
        self.vertices = (
            left_side_bearing,
            -baseline,
            left_side_bearing + self.width,
            -baseline + self.height)

    def draw(self):
        '''Debug method: use the higher level APIs for performance and
        kerning.'''
        glBindTexture(GL_TEXTURE_2D, self.texture.id)
        glBegin(GL_QUADS)
        self.draw_quad_vertices()
        glEnd()

    def draw_quad_vertices(self):
        '''Debug method: use the higher level APIs for performance and
        kerning.'''
        glTexCoord2f(self.tex_coords[0], self.tex_coords[1])
        glVertex2f(self.vertices[0], self.vertices[1])
        glTexCoord2f(self.tex_coords[2], self.tex_coords[1])
        glVertex2f(self.vertices[2], self.vertices[1])
        glTexCoord2f(self.tex_coords[2], self.tex_coords[3])
        glVertex2f(self.vertices[2], self.vertices[3])
        glTexCoord2f(self.tex_coords[0], self.tex_coords[3])
        glVertex2f(self.vertices[0], self.vertices[3])

    def get_kerning_pair(self, right_glyph):
        return 0

class GlyphTextureAtlas(AllocatingTextureAtlas):
    subimage_class = Glyph

    def apply_blend_state(self):
        # Subclasses should override
        pass

class StyledText(object):
    '''One contiguous sequence of characters sharing the same
    GL state.  It is up to the caller to ensure all glyphs share
    the same owning texture (Font.get_styled_text_list does this).'''
    def __init__(self, glyphs, texture, color=(1, 1, 1, 1)):
        assert len(color) == 4
        assert isinstance(texture, GlyphTextureAtlas)
        self.glyphs = glyphs
        self.texture = texture
        self.color = color

class TextLayout(object):
    '''Will eventually handle all complex layout, line breaking,
    justification and state sorting/coalescing.'''
    def __init__(self, styled_texts):
        self.styled_texts = styled_texts

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        for styled_text in self.styled_texts:
            # Complete GL state for this style run
            glBindTexture(GL_TEXTURE_2D, styled_text.texture.id)
            styled_text.texture.apply_blend_state()
            glColor4f(*styled_text.color)

            # And draw the (by now kerned, positioned) text.
            # This looks silly now, but prepping for more efficient
            # VBO/arrays (proving bound texture state is correct).
            for glyph in styled_text.glyphs:
                glBegin(GL_QUADS)
                glyph.draw_quad_vertices()
                glEnd()   
                glTranslatef(glyph.advance, 0, 0)
        glPopMatrix()
        glPopAttrib()

class GlyphRenderer(object):
    def __init__(self, font):
        pass

    def render(self, text):
        raise NotImplementedError('Subclass must override')


class FontException(Exception):
    pass

class BaseFont(object):
    texture_width = 256
    texture_height = 256
    texture_internalformat = GL_LUMINANCE_ALPHA

    # These two need overriding by subclasses
    glyph_texture_atlas_class = GlyphTextureAtlas
    glyph_renderer_class = GlyphRenderer

    def __init__(self):
        self.textures = []
        self.glyphs = {}

    @classmethod
    def add_font_data(cls, data):
        # Ignored unless overridden
        pass

    def allocate_glyph(self, width, height):
        # Search atlases for a free spot
        for texture in self.textures:
            try:
                return texture.allocate(width, height)
            except AllocatingTextureAtlasOutOfSpaceException:
                pass

        # If requested glyph size is bigger than atlas size, increase
        # next atlas size.  A better heuristic could be applied earlier
        # (say, if width is > 1/4 texture_width).
        if width > self.texture_width or height > self.texture_height:
            self.texture_width, self.texture_height, u, v= \
                Texture.get_texture_size(width * 2, height * 2)

        texture = self.glyph_texture_atlas_class.create(
            self.texture_width,
            self.texture_height,
            self.texture_internalformat)
        self.textures.insert(0, texture)

        # This can't fail.
        return texture.allocate(width, height)

    def get_glyphs(self, text):
        glyph_renderer = None
        for c in text:
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.glyph_renderer_class(self)
                self.glyphs[c] = glyph_renderer.render(c)
        return [self.glyphs[c] for c in text] 

    def get_styled_text_list(self, text, color):
        texture = None
        result = []
        for glyph in self.get_glyphs(text):
            if glyph.texture != texture:
                glyph_list = []
                result.append(StyledText(glyph_list, glyph.texture, color))
                texture = glyph.texture
            glyph_list.append(glyph)
        return result

    def render(self, text, color=(1, 1, 1, 1)):
        return TextLayout(self.get_styled_text_list(text, color))

# Load platform dependent module
if sys.platform == 'darwin':
    from pyglet.text.carbon import CarbonFont
    _font_class = CarbonFont
elif sys.platform == 'win32':
    from pyglet.text.win32 import Win32Font
    _font_class = Win32Font
else:
    from pyglet.text.freetype import FreeTypeFont
    _font_class = FreeTypeFont

class Font(object):
    def __new__(cls, name, size, bold=False, italic=False):
        # TODO: Cache fonts, lookup bitmap fonts.
        return _font_class(name, size, bold=bold, italic=italic)

    @staticmethod
    def add_font(font):
        if type(font) in (str, unicode):
            font = open(font, 'r')
        if hasattr(font, 'read'):
            font = font.read()
        _font_class.add_font_data(font)


    @staticmethod
    def add_font_dir(dir):
        import os
        for file in os.listdir(dir):
            if file[:-4].lower() == '.ttf':
                add_font(file)


