#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.GL.VERSION_1_1 import *
import pyglet.text
from pyglet.layout.base import *

class GLRenderDevice(RenderDevice):
    _stock_font_names = {
        'serif':        'Bitstream Vera Serif',
        'sans-serif':   'Bitstream Vera Sans',
        'monospace':    'Bitstream Vera Sans Mono',
        'fantasy':      'Bistream Vera Serif',
        'cursive':      'Bistream Vera Serif',
    }

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
        return pyglet.text.Font(names, size, italic=italic, bold=bold)

    def create_inline_text_boxes(self, font, text):
        return font.get_inline_boxes(text)

    def draw_vertical_border(self, x1, y1, x2, y2, color, style):
        if style != 'solid':
            raise NotImplementedError()

        glColor4f(*color)
        glBegin(GL_QUADS)
        glVertex2f(x1, y1)
        glVertex2f(x1, y2)
        glVertex2f(x2, y2)
        glVertex2f(x2, y1)
        glEnd()

    draw_horizontal_border = draw_vertical_border

    def draw_background(self, x1, y1, x2, y2, box):
        if box.background_color == 'transparent':
            return

        glColor4f(*box.background_color)
        glBegin(GL_QUADS)
        glVertex2f(x1, y1)
        glVertex2f(x1, y2)
        glVertex2f(x2, y2)
        glVertex2f(x2, y1)
        glEnd()
    
