#!/usr/bin/env python

'''

TODO in near future:
 - Layout (wrapping)
     - StyledText needs width,height,advance,ascent,descent
     - StyledText needs word breaks
 - Kerning
 - Tracking
 - Character spacing

TODO much later:
 - BIDI
 - Vertical text
 - Path following?
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import os

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *

# Source: http://www.cs.tut.fi/~jkorpela/chars/spaces.html
_word_spaces = (u'\u0020\u00a0\u2000\u2001\u2002\u2003\u2004\u2005\u2006' +
                u'\u2007\u2008\u2009\u200a\u200b\u202f\u205f\u205f\u3000' +
                u'\ufeff')

class Glyph(TextureSubImage):
    advance = 0
    vertices = (0, 0, 0, 0)

    # possibility for future: is_kashida
    is_word_space = False

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
    the same owning texture (Font.get_styled_text_list does this).
    
    This is slightly low-level, used only by TextLayout, not directly
    by applications.
    '''
    array = None
    glyph_positions = None

    def __init__(self, glyphs, font, texture, color=(1, 1, 1, 1)):
        assert len(color) == 4
        assert isinstance(texture, GlyphTextureAtlas)
        self.glyphs = glyphs
        self.font = font
        self.texture = texture
        self.color = color

    def create_array(self):
        if self.array:
            return

        # Create an interleaved array in GL_T2F_V3F format
        self.glyph_positions = []
        lst = []
        x = 0
        for glyph in self.glyphs:
            self.glyph_positions.append(x)
            lst += [glyph.tex_coords[0], glyph.tex_coords[1],
                    x + glyph.vertices[0], glyph.vertices[1], 0.,
                    glyph.tex_coords[2], glyph.tex_coords[1],
                    x + glyph.vertices[2], glyph.vertices[1], 0.,
                    glyph.tex_coords[2], glyph.tex_coords[3],
                    x + glyph.vertices[2], glyph.vertices[3], 0.,
                    glyph.tex_coords[0], glyph.tex_coords[3],
                    x + glyph.vertices[0], glyph.vertices[3], 0.]
            x += glyph.advance
        self.array = (c_float * (5 * 4 * len(self.glyphs)))(*lst)
        self.advance = x

    def draw(self, begin=0, end=None):
        if end is None:
            end = len(self.glyphs)

        glPushMatrix()
        glTranslatef(-self.glyph_positions[begin], 0, 0)
        if not self.array:
            self.create_array()
        glInterleavedArrays(GL_T2F_V3F, 0, self.array)
        # Number of quads, not glyphs
        glDrawArrays(GL_QUADS, begin * 4, (end - begin) * 4)
        glPopMatrix()

    def get_width(self):
        self.create_array()
        return self.advance
    width = property(get_width)

    def get_ascent(self):
        return self.font.ascent
    ascent = property(get_ascent)
    
    def get_descent(self):
        return self.font.descent
    descent = property(get_descent)

    def get_break_index(self, begin, width):
        '''Return `index`, `hard_index` >= `begin` and such that all glyphs in
        range [begin:index] can be rendered into `width` pixels without
        clipping.  Similarly for hard_index, except spaces are ignored.
        Return None if there are no breakpoints in range.'''
        self.create_array()

        width += self.glyph_positions[begin]

        break_index = None
        for i, glyph in enumerate(self.glyphs[begin:]):
            if self.glyph_positions[begin + i] > width:
                break
            if glyph.is_word_space:
                break_index = begin + i
        return break_index, begin + i - 1

    def get_range_width(self, begin, end):
        '''Return width of glyphs between `begin` and `end`.'''
        if not end or end == len(self.glyphs) - 1:
            return self.width - self.glyph_positions[begin]
        return self.glyph_positions[end + 1] - self.glyph_positions[begin]


class TextLayoutLine(object):
    def __init__(self, styled_texts, begin=0, end=None):
        self.styled_texts = styled_texts
        self.begin = begin
        self.end = end
        self.ascent = max([t.ascent for t in styled_texts])
        self.descent = min([t.descent for t in styled_texts])

    def __repr__(self):
        # DEBUG
        s = ''
        begin = self.begin
        end = None
        last = len(self.styled_texts) - 1
        for i, styled_text in enumerate(self.styled_texts):
            if i == last:
                end = self.end

            s += ''.join([g.character for g in styled_text.glyphs[begin:end]])
            begin = 0
        return s

    def draw(self):
        begin = self.begin
        end = None
        last = len(self.styled_texts) - 1
        for i, styled_text in enumerate(self.styled_texts):
            if i == last:
                end = self.end

            # Complete GL state for this style run
            glBindTexture(GL_TEXTURE_2D, styled_text.texture.id)
            styled_text.texture.apply_blend_state()
            glColor4f(*styled_text.color)

            # Draw and move cursor
            styled_text.draw(begin, end)
            glTranslatef(styled_text.advance, 0, 0) 
            begin = 0 

class TextLayout(object):
    # If None, no wrapping is done.
    _wrap_width = None

    # Cached layout lines
    _lines = None

    def __init__(self, styled_texts):
        self.styled_texts = styled_texts

    def layout(self):
        # Simple case of no wrapping
        if not self._wrap_width:
            self._lines = [TextLayoutLine(self.styled_texts)]
            return

        # Completed typeset TextLayoutLine's
        self._lines = []

        # StyledTexts that fit within the current line.  The first one
        # contains `begin` index.  The last one contains `break_index`.
        line_runs = []

        # Glyph index within first StyledText in `line_runs` 
        # that starts the line.
        begin = 0

        # Glyph index within current `run`, == begin if this
        # is first StyledText in `line_runs`, otherwise == 0.
        local_begin = 0

        # Glyph index within last StyledText in `line_runs`
        # that breaks the line validly.
        break_index = None

        # StyledTexts that fit within the current line after
        # `line_runs`, only if a valid break will be encountered later.
        pending = []

        # Width, in pixels, of current line remaining to be typeset.
        remaining_width = self._wrap_width

        runs = self.styled_texts[:]
        while len(runs):
            run = runs.pop(0)

            bp, hbp = run.get_break_index(local_begin, remaining_width)
            if bp:
                # Found a valid breakpoint.  Everything before
                # this breakpoint, in pending, can be committed to the
                # line now, as can `run`.
                break_index = bp
                line_runs += pending
                line_runs.append(run)
                pending = []

            if (run.get_range_width(local_begin, None) < remaining_width):
                # The entire `run[local_begin:]` fits on
                # the line, add it to `pending` if it is not yet committed.
                if run not in line_runs:
                    pending.append(run)

                # Subtract its width from remaining line width.
                remaining_width -= run.get_range_width(local_begin, None)

                # Grab the next StyledText.
                local_begin = 0

                # This is the only exit point of the loop, as every execution
                # path afterwards pushes something back into `runs`.
                continue

            # A break is needed somewhere in line_runs or pending.
            if break_index:
                # Luckly, there is a valid breakpoint defined in 
                # `line_runs`.  Ignore everything after it
                # (in `pending`).
                line = TextLayoutLine(line_runs, begin, break_index)
                self._lines.append(line)

                # Start next line after break.
                local_begin = begin = break_index + 1
                break_index = 0
                remaining_width = self._wrap_width

                # Push pending and run back into runs.
                runs = [run,] + pending + runs
                line_runs = []
                pending = []
            else:
                # There was no valid breakpoint on this line.  Split it
                # at the last found hard breakpoint (hbp), which is in 
                # current `run`.
                line_runs += pending + [run,]

                if hbp <= local_begin:
                    # Not even a single glyph fits; let it overrun.
                    hbp += 1
                line = TextLayoutLine(line_runs, begin, hbp)
                self._lines.append(line)

                local_begin = begin = hbp
                break_index = 0
                remaining_width = self._wrap_width

                runs = [run,] + pending + runs
                line_runs = []
                pending = []

        # Add final line
        assert remaining_width > 0
        line_runs += pending
        if line_runs:
            line = TextLayoutLine(line_runs, begin, None)
            self._lines.append(line)

    def draw(self):
        if self._lines is None:
            self.layout()

        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        for i, line in enumerate(self._lines):
            if i != 0: 
                # Draw first line at baseline
                glTranslatef(0, -line.ascent, 0)
            glPushMatrix()
            line.draw()
            glPopMatrix()
            glTranslatef(0, line.descent, 0)
        glPopMatrix()
        glPopAttrib()

    # Word-wrap width can be set or unset
    def get_width(self):
        if self._wrap_width:
            return self._wrap_width
        else:
            return sum([t.width for t in self.styled_texts])
    def set_width(self, width):
        self._wrap_width = width
        self._lines = None
    def disable_wrap(self):
        self._wrap_width = None
        self._lines = None
    width = property(get_width, set_width, disable_wrap)


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

    # These should also be set by subclass when known
    ascent = 0
    descent = 0

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
                if c in _word_spaces:
                    self.glyphs[c].is_word_space = True
                
                # DEBUG
                self.glyphs[c].character = c
        return [self.glyphs[c] for c in text] 

    def get_styled_text_list(self, text, color):
        texture = None
        result = []
        glyph_list = []
        for glyph in self.get_glyphs(text):
            if glyph.texture != texture:
                if glyph_list:
                    result.append(StyledText(glyph_list, self, texture, color))
                glyph_list = []
                texture = glyph.texture
            glyph_list.append(glyph)
        result.append(StyledText(glyph_list, self, texture, color))
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


