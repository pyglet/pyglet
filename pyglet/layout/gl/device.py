#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.GL.VERSION_1_1 import *
import pyglet.text
from pyglet.layout.base import *
from pyglet.layout.locator import *
from pyglet.layout.visual import *
from pyglet.image import *

class GLFont(object):
    def __init__(self, font):
        self.font = font

    def create_text_frame(self, box, parent, containing_block,
                          text, width):
        glyphs = self.font.get_glyphs_for_width(text, width)

        # Find state changes required in glyph list.
        texture = None
        states = []
        state_from = 0
        state_length = 0
        for i, glyph in enumerate(glyphs):
            if glyph.texture != texture:
                if state_length:
                    states.append((state_from, state_length, texture))
                texture = glyph.texture
                state_from = i
                state_length = 0
            state_length += 1
        states.append((state_from, state_length, texture))
        frame = GLTextFrame(box, parent, containing_block, 
            self.font, text[:len(glyphs)], glyphs, states)
        
        if len(text) > len(glyphs) and text[len(glyphs)] == '\n':
            frame.hard_break = True

        return frame

class GLRenderDevice(RenderDevice):
    _stock_font_names = {
        'serif':        'Bitstream Vera Serif',
        'sans-serif':   'Bitstream Vera Sans',
        'monospace':    'Bitstream Vera Sans Mono',
        'fantasy':      'Bistream Vera Serif',
        'cursive':      'Bistream Vera Serif',
    }

    def __init__(self, locator=LocalFileLocator):
        self.locator = locator
        self.texture_cache = {}

    def get_font(self, box):
        names = (box.font_family or [])[:]

        for i, name in enumerate(names):
            if isinstance(name, Ident) and name in self._stock_font_names:
                names[i] = self._stock_font_names[name]

        size = box.font_size
        italic = box.font_style == 'italic'
        bold = box.font_weight >= 700

        if isinstance(size, Dimension):
            if size.unit == 'pt':
                size = size
            else:
                raise NotImplementedError()
        elif size == 'medium':
            size = 12
        else:
            raise NotImplementedError()
        return GLFont(pyglet.text.Font(names, size, italic=italic, bold=bold))


    def draw_solid_border(self, x1, y1, x2, y2, x3, y3, x4, y4, 
                          color, style):
        '''Draw one side of a border, which is not 'dotted' or 'dashed'.
        '''
        glColor4f(*color)
        glBegin(GL_QUADS)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glVertex2f(x3, y3)
        glVertex2f(x4, y4)
        glEnd()


    def draw_vertical_border(self, x1, y1, x2, y2, x3, y3, x4, y4,
                             color, style):
        '''Draw one vertical edge of a border.
        
        Order of vertices is inner-top, inner-bottom, outer-bottom, outer-top
        '''
        if style in ('dotted', 'dashed'):
            width = max(abs(x1 - x4), 1)
            height = y1 - y2
            if style == 'dotted':
                period = width
            else:
                period = width * 3
            cycles = int(height / period)
            padding = (height - cycles * period) / 2
            vertices = [
                # Top cap
                x1, y1, x1, y1 - padding, x4, y1 - padding, x4, y4,
                # Bottom cap
                x2, y2, x2, y2 + padding, x3, y2 + padding, x3, y3]
            y = y1 - padding
            phase = cycles % 2
            if phase == 0:
                y -= period / 2
            for i in range(cycles):
                if i % 2 == phase:
                    vertices += [x1, y, x1, y - period, x3, y - period, x3, y]
                y -= period
            self.vertices = (c_float * len(vertices))(*vertices)
            glColor4f(*color)
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(2, GL_FLOAT, 0, self.vertices)
            glDrawArrays(GL_QUADS, 0, len(self.vertices)/2)
            glPopClientAttrib()
        else:
            self.draw_solid_border(x1, y1, x2, y2, x3, y3, x4, y4, color, style)

    def draw_horizontal_border(self, x1, y1, x2, y2, x3, y3, x4, y4,
                               color, style):
        '''Draw one horizontal edge of a border.
        
        Order of vertices is inner-left, inner-right, outer-right, outer-left.
        '''
        if style in ('dotted', 'dashed'):
            height = max(abs(y1 - y4), 1)
            width = x2 - x1
            if style == 'dotted':
                period = height 
            else:
                period = height * 3
            cycles = int(width / period)
            padding = (width - cycles * period) / 2
            vertices = [
                # Left cap
                x1, y1, x1 + padding, y1, x1 + padding, y4, x4, y4,
                # Right cap
                x2, y2, x2 - padding, y2, x2 - padding, y3, x3, y3]
            x = x1 + padding
            phase = cycles % 2
            if phase == 0:
                x += period / 2
            for i in range(cycles):
                if i % 2 == phase:
                    vertices += [x, y1, x + period, y1, x + period, y3, x, y3]
                x += period
            self.vertices = (c_float * len(vertices))(*vertices)
            glColor4f(*color)
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(2, GL_FLOAT, 0, self.vertices)
            glDrawArrays(GL_QUADS, 0, len(self.vertices)/2)
            glPopClientAttrib()
        else:
            self.draw_solid_border(x1, y1, x2, y2, x3, y3, x4, y4, color, style)

    def draw_background(self, x1, y1, x2, y2, box):
        if box.background_color != 'transparent':
            glPushAttrib(GL_CURRENT_BIT)
            glColor4f(*box.background_color)
            glBegin(GL_QUADS)
            glVertex2f(x1, y1)
            glVertex2f(x1, y2)
            glVertex2f(x2, y2)
            glVertex2f(x2, y1)
            glEnd()
            glPopAttrib()

        if box.background_image != 'none':
            if box.background_image not in self.texture_cache:
                self.texture_cache[box.background_image] = None
                stream = self.locator.get_stream(box.background_image)
                if stream:
                    texture = Image.load(file=stream).texture()
                    if box.background_repeat != 'no-repeat':
                        texture.stretch()
                    self.texture_cache[box.background_image] = texture
            texture = self.texture_cache[box.background_image]
            if texture:
                u1, v1 = 0,0
                u2, v2 = texture.uv
                width, height = texture.width, texture.height
                repeat = box.background_repeat
                if repeat in ('no-repeat', 'repeat-y'):
                    x2 = x1 + width
                else:
                    u2 = (x2 - x1) / width

                if repeat in ('no-repeat', 'repeat-x'):
                    y2 = y1 - height
                else:
                    v2 = (y1 - y2) / height
                    # Compensate to keep tiling beginning at top, not bottom
                    v1 = -(v2 - int(v2))
                    v2 += v1

                      # uv          # xyz
                ar = [u1, v1,       x1, y2, 0,
                      u1, v2,       x1, y1, 0,
                      u2, v2,       x2, y1, 0,
                      u2, v1,       x2, y2, 0]
                ar = (c_float * len(ar))(*ar)
            
                glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
                glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
                glColor3f(1, 1, 1)
                glEnable(GL_TEXTURE_2D)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glBindTexture(GL_TEXTURE_2D, texture.id)
                glInterleavedArrays(GL_T2F_V3F, 0, ar)
                glDrawArrays(GL_QUADS, 0, 4)
                glPopAttrib()
                glPopClientAttrib()
                    
   
class GLTextFrame(TextFrame):
    '''One contiguous sequence of characters.  The characters must belong
    to the same font, but may have different glyph textures.
    '''
    hard_break = False

    def __init__(self, box, parent, containing_block,
                 font, text, glyphs, states):
        # We currently make this assumption in draw and measure methods.
        # It is not required by the interface, but is currently implemented
        # as such.
        assert len(text) == len(glyphs)

        self.text = text
        self.glyphs = glyphs
        self.states = states
        self.font = font

        # Create an interleaved array in GL_T2F_V3F format
        lst = []
        x = 0
        for glyph in self.glyphs:
            lst += [glyph.tex_coords[0], glyph.tex_coords[1],
                    x + glyph.vertices[0], glyph.vertices[1], 0.,
                    glyph.tex_coords[2], glyph.tex_coords[1],
                    x + glyph.vertices[2], glyph.vertices[1], 0.,
                    glyph.tex_coords[2], glyph.tex_coords[3],
                    x + glyph.vertices[2], glyph.vertices[3], 0.,
                    glyph.tex_coords[0], glyph.tex_coords[3],
                    x + glyph.vertices[0], glyph.vertices[3], 0.]
            x += glyph.advance
        self.array = (c_float * len(lst))(*lst)

        # CSS properties
        self.text_width = x
        self.text_ascent = font.ascent
        self.text_descent = font.descent

        super(GLTextFrame, self).__init__(box, parent, containing_block, text)


    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.text)

    def draw_text(self, render_context, x, y):
        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)

        # XXX Safe to assume all required textures will use same blend state I
        # think.  (otherwise move this into loop)
        self.states[0][2].apply_blend_state()

        glColor4f(*self.box.color)
        glPushMatrix()
        glTranslatef(x, y, 0)
        glInterleavedArrays(GL_T2F_V3F, 0, self.array)
        for state_from, state_length, texture in self.states:
            glBindTexture(GL_TEXTURE_2D, texture.id)
            glDrawArrays(GL_QUADS, state_from * 4, state_length * 4)
        glPopMatrix()
        glPopAttrib()
 
