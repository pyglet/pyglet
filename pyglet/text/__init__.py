#!/usr/bin/env python

'''

TODO in near future:
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
from pyglet.window import *
from pyglet.image import *
import pyglet.layout.base

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
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

class TextBox(pyglet.layout.base.Box):
    '''One contiguous sequence of characters sharing the same
    GL state.  It is up to the caller to ensure all glyphs share
    the same owning texture (Font.get_styled_text_list does this).
    
    This is slightly low-level, used only by TextLayout and pyglet.layout, 
    not directly by applications.
    '''
    array = None
    glyph_positions = None

    # CSS properties
    is_text = True

    def __init__(self, text, glyphs, font, texture):
        # GlyphTextureAtlas defines apply_blend_state function.
        assert isinstance(texture, GlyphTextureAtlas)

        # We currently make this assumption in draw and measure methods.
        # It is not required by the interface, but is currently implemented
        # as such.
        assert len(text) == len(glyphs)

        self.text = text
        self.glyphs = glyphs
        self.font = font
        self.texture = texture

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

        # CSS properties
        self.intrinsic_width = x
        self.intrinsic_ascent = font.ascent
        self.intrinsic_descent = font.descent

    def __repr__(self):
        d = self.__dict__.copy()
        del d['array']
        del d['glyphs']
        del d['glyph_positions']
        del d['texture']
        del d['text']
        #return '%s(%r, %r)' % (self.__class__.__name__, self.text, d)
        return '%s(%r)' % (self.__class__.__name__, self.text)

    def get_text(self):
        return self.text

    def get_breakpoint(self, from_breakpoint, break_characters, width):
        width += self.glyph_positions[from_breakpoint]

        breakpoint = None
        for i, glyph in enumerate(self.glyphs[from_breakpoint:]):
            if (self.glyph_positions[from_breakpoint + i] > width and 
                breakpoint is not None):
                break
            if self.text[from_breakpoint + i] in break_characters:
                breakpoint = from_breakpoint + i
        return breakpoint

    def get_region_width(self, from_breakpoint, to_breakpoint):
        if not to_breakpoint or to_breakpoint >= len(self.glyphs):
            return self.intrinsic_width - self.glyph_positions[from_breakpoint]
        return self.glyph_positions[to_breakpoint] - \
               self.glyph_positions[from_breakpoint]

    def draw(self, render_context, left, top, right, bottom):
        self.draw_region(left, top, right, bottom, None, None)

    def draw_region(self, render_context, left, top, right, bottom, 
                    from_breakpoint, to_breakpoint):
        if from_breakpoint is None:
            from_breakpoint = 0
        if to_breakpoint is None:
            to_breakpoint = len(self.glyphs)

        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture.id)
        self.texture.apply_blend_state()
        glColor4f(*self.color)
        glPushMatrix()
        glTranslatef(-self.glyph_positions[from_breakpoint] + left, top, 0)
        glInterleavedArrays(GL_T2F_V3F, 0, self.array)
        # Number of quads, not glyphs
        glDrawArrays(GL_QUADS, from_breakpoint * 4, 
                     (to_breakpoint - from_breakpoint) * 4)
        glPopMatrix()
        glPopAttrib()



class TextLayoutLine(object):
    def __init__(self, text_boxes, begin=0, end=None):
        self.text_boxes = text_boxes
        self.begin = begin
        self.end = end
        self.ascent = max([t.font.ascent for t in text_boxes])
        self.descent = min([t.font.descent for t in text_boxes])

    def __repr__(self):
        # DEBUG
        s = ''
        begin = self.begin
        end = None
        last = len(self.text_boxes) - 1
        for i, text_box in enumerate(self.text_boxes):
            if i == last:
                end = self.end
            s += text_box.text[begin:end]
            begin = 0
        return s

    def draw(self):
        begin = self.begin
        end = None
        last = len(self.text_boxes) - 1
        for i, text_box in enumerate(self.text_boxes):
            if i == last:
                end = self.end

            # Draw and move cursor
            text_box.draw_region(None, 0, 0, 0, 0, begin, end)
            glTranslatef(text_box.get_region_width(begin, end), 0, 0) 
            begin = 0 

class TextLayout(object):
    # If None, no wrapping is done.
    _wrap_width = None

    # Cached layout lines
    _lines = None

    def __init__(self, text_boxes):
        self.text_boxes = text_boxes

    def layout(self):
        # Simple case of no wrapping
        if not self._wrap_width:
            self._lines = [TextLayoutLine(self.text_boxes)]
            return

        # Completed typeset TextLayoutLine's
        self._lines = []

        # TextBox's that fit within the current line.  The first one
        # contains `begin` index.  The last one contains `break_index`.
        line_runs = []

        # Glyph index within first TextBox in `line_runs` 
        # that starts the line.
        begin = 0

        # Glyph index within current `run`, == begin if this
        # is first TextBox in `line_runs`, otherwise == 0.
        local_begin = 0

        # Glyph index within last TextBox in `line_runs`
        # that breaks the line validly.
        break_index = None

        # TextBox's that fit within the current line after
        # `line_runs`, only if a valid break will be encountered later.
        pending = []

        # Width, in pixels, of current line remaining to be typeset.
        remaining_width = self._wrap_width

        runs = self.text_boxes[:]
        while len(runs):
            run = runs.pop(0)

            bp = run.get_breakpoint(local_begin, ' ', remaining_width)
            hbp = run.get_breakpoint(local_begin, '\n', remaining_width)
            if bp:
                # Found a valid breakpoint.  Everything before
                # this breakpoint, in pending, can be committed to the
                # line now, as can `run`.
                break_index = bp
                line_runs += pending
                line_runs.append(run)
                pending = []

            if (run.get_region_width(local_begin, None) < remaining_width):
                # The entire `run[local_begin:]` fits on
                # the line, add it to `pending` if it is not yet committed.
                if run not in line_runs:
                    pending.append(run)

                # Subtract its width from remaining line width.
                remaining_width -= run.get_region_width(local_begin, None)

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
            return sum([t.intrinsic_width for t in self.text_boxes])
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
    texture_internalformat = GL_ALPHA

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

    @classmethod
    def have_font(cls, name):
        # Subclasses override
        return True

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
                
                # DEBUG
                self.glyphs[c].character = c
        return [self.glyphs[c] for c in text] 

    def get_inline_boxes(self, text):
        texture = None
        result = []
        glyph_list = []
        begin = 0
        end = 0
        for glyph in self.get_glyphs(text):
            if glyph.texture != texture:
                if glyph_list:
                    result.append(
                        TextBox(text[begin:end], glyph_list, self, texture))
                    begin = end 
                glyph_list = []
                texture = glyph.texture
            glyph_list.append(glyph)
            end += 1
        result.append(TextBox(text[begin:end], glyph_list, self, texture))
        return result

    def render(self, text, color=(1, 1, 1, 1)):
        boxes = self.get_inline_boxes(text)
        for box in boxes:
            box.color = color
        return TextLayout(boxes)

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
        # Find first matching name
        if type(name) in (tuple, list):
            for n in name:
                if _font_class.have_font(n):
                    name = n
                    break
            else:
                name = None
    
        # Locate or create font cache   
        shared_object_space = get_current_context().get_shared_object_space()
        if not hasattr(shared_object_space, 'pyglet_text_font_cache'):
            shared_object_space.pyglet_text_font_cache = {}
        font_cache = shared_object_space.pyglet_text_font_cache

        # Look for font name in font cache
        descriptor = (name, size, bold, italic)
        if descriptor in font_cache:
            return font_cache[descriptor]

        # Not in cache, create from scratch
        font = _font_class(name, size, bold=bold, italic=italic)
        font_cache[descriptor] = font
        return font

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


