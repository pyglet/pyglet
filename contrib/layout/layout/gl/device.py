#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
import re

from pyglet.gl import *
import pyglet.font

from layout.base import *
from layout.frame import *
from layout.locator import *

from pyglet import image

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

    def get_font(self, names, size, style, weight):
        names = names[:]

        for i, name in enumerate(names):
            if isinstance(name, Ident) and name in self._stock_font_names:
                names[i] = self._stock_font_names[name]

        italic = style == 'italic'
        bold = weight >= 700
        assert type(size) == Dimension and size.unit == 'pt'

        return pyglet.font.load(names, size, italic=italic, bold=bold)

    def create_text_frame(self, style, element, text):
        return GLTextFrame(style, element, text)

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

    def draw_background(self, x1, y1, x2, y2, frame):
        compute = frame.get_computed_property
        background_color = compute('background-color')
        if background_color != 'transparent':
            glPushAttrib(GL_CURRENT_BIT)
            glColor4f(*background_color)
            glBegin(GL_QUADS)
            glVertex2f(x1, y1)
            glVertex2f(x1, y2)
            glVertex2f(x2, y2)
            glVertex2f(x2, y1)
            glEnd()
            glPopAttrib()

        background_image = compute('background-image')
        if background_image != 'none':
            repeat = compute('background-repeat')
            # TODO tileable texture in cache vs non-tileable, vice-versa
            if background_image not in self.texture_cache:
                self.texture_cache[background_image] = None
                stream = self.locator.get_stream(background_image)
                if stream:
                    img = image.load('', file=stream)
                    if repeat != 'no-repeat':
                        texture = image.TileableTexture.create_for_image(img)
                    else:
                        texture = img.texture
                    self.texture_cache[background_image] = texture
            texture = self.texture_cache[background_image]
            if texture:
                glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
                glColor3f(1, 1, 1)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                if isinstance(texture, image.TileableTexture):
                    width, height = texture.width, texture.height
                    if repeat in ('repeat', 'repeat-x'):
                        width = x2 - x1
                    if repeat in ('repeat', 'repeat-y'):
                        height = y1 - y2
                    texture.blit_tiled(x1, y2, 0, width, height)
                else:
                    texture.blit(x1, y2, 0)
                glPopAttrib()
   
class GLTextFrame(TextFrame):
    glyph_string = None
    from_index = 0
    to_index = None

    content_ascent = 0

    def __init__(self, style, element, text):
        super(GLTextFrame, self).__init__(style, element, text)

    def lstrip(self):
        text = self.text[self.from_index:self.to_index]
        old_index = self.from_index
        self.from_index += len(text) - len(text.lstrip())
        if old_index != self.from_index:
            self.border_edge_width -= self.glyph_string.get_subwidth(
                old_index, self.from_index)


    contains_ws = re.compile(u'[\n\u0020\u200b]')

    def purge_style_cache(self, properties):
        super(GLTextFrame, self).purge_style_cache(properties)
        if ('font-name' in properties or
            'font-size' in properties or
            'font-weight' in properties or
            'font-style' in properties):
            self.glyph_string = None

    def flow_inline(self, context):
        context = context.copy()

        # Reset after last flow
        self.from_index = 0
        self.strip_next = False
        self.continuation = None
        self.close_border = True
        
        # Final white-space processing step (besides line beginning strip)
        # from 16.6.1 step 4.
        if context.strip_next and \
           self.get_computed_property('white-space') in \
               ('normal', 'nowrap', 'pre-line'):
            self.from_index = len(self.text) - len(self.text.lstrip())

        # Get GL glyph sequence if not already cached
        font = self.get_computed_property('--font')
        if not self.glyph_string:
            self.glyph_string = pyglet.font.GlyphString(
                self.text, font.get_glyphs(self.text))

        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                value = value * self.containing_block.width
            return value
        
        # Calculate computed and used values of box properties when
        # relative to containing block width.
        # margin top/bottom remain at class default 0
        content_right = computed('border-right-width') + used('padding-right')
        content_bottom = computed('border-bottom-width') + \
            used('padding-bottom')
        self.content_top = computed('border-top-width') + used('padding-top')
        self.margin_right = used('margin-right')
        self.margin_left = used('margin-left')
        self.content_left = computed('border-left-width') + used('padding-left')

        # Calculate text metrics (actually not dependent on flow, could
        # optimise out).
        self.content_ascent = font.ascent
        self.content_descent = font.descent
        line_height = self.get_computed_property('line-height') 
        if line_height != 'normal':
            half_leading = (line_height - \
                (self.content_ascent - self.content_descent)) / 2
        else:
            half_leading = 0
        self.line_ascent = self.content_ascent + half_leading
        self.line_descent = self.content_descent - half_leading
        self.border_edge_height = self.content_ascent - self.content_descent +\
            self.content_top + content_bottom
        self.border_edge_width = self.content_left
        self.baseline = self.content_ascent + self.content_top

        context.add(self.margin_left + self.content_left)
        context.reserve(content_right + self.margin_right)

        # Break into continuations
        frame = self
        while True:
            frame.to_index = self.glyph_string.get_break_index(
                frame.from_index, 
                context.remaining_width - context.reserved_width)

            if frame.to_index == frame.from_index:
                ws = self.contains_ws.search(self.text[frame.from_index:])
                if ws:
                    frame.to_index = frame.from_index + ws.start() + 1
                else:
                    frame.to_index = len(self.text)

            text_width = self.glyph_string.get_subwidth(
                frame.from_index, frame.to_index) 
            frame.border_edge_width += text_width

            if frame.to_index < len(self.text):
                continuation = GLTextFrame(
                    self.style, self.element, self.text)
                continuation.parent = self.parent
                continuation.glyph_string = self.glyph_string
                continuation.open_border = False
                continuation.from_index = continuation.to_index = frame.to_index

                continuation.border_edge_height = self.border_edge_height
                continuation.border_edge_width = 0
                continuation.margin_right = self.margin_right
                continuation.line_ascent = self.line_ascent
                continuation.line_descent = self.line_descent
                continuation.content_ascent = self.content_ascent
                continuation.content_descent = self.content_descent
                continuation.baseline = self.baseline

                # Remove right-margin from continued frame
                frame.margin_right = 0

                if not context.can_add(text_width, True):  
                    context.newline()
                context.add(text_width)
                context.breakpoint()
                frame.soft_break = True

                # Force line break
                if frame.to_index and self.text[frame.to_index-1] == '\n':
                    frame.to_index -= 1
                    frame.line_break = True
                    context.newline()

                # Ready for next iteration
                frame.continuation = continuation
                frame.close_border = False
                frame = continuation
                context.newline()

            if frame.to_index >= len(self.text):
                break

        frame.strip_next = self.text[-1] == ' '
        frame.soft_break = self.text[-1] == ' '
        frame.border_edge_width += content_right
        self.flow_dirty = False


    def draw_text(self, x, y, render_context):
        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glColor4f(*self.get_computed_property('color'))
        glPushMatrix()
        glTranslatef(x, y, 0)
        self.glyph_string.draw(self.from_index, self.to_index)
        glPopMatrix()
        glPopAttrib()
 
    def __repr__(self):
        return '%s(%r)' % \
            (self.__class__.__name__, self.text[self.from_index:self.to_index])
