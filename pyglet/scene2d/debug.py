#!/usr/bin/env python

'''
Simple images etc. to aid debugging
===================================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.scene2d import *
from pyglet.image import Image
from pyglet.scene2d.drawable import *
from pyglet.GL.VERSION_1_1 import *

cell = HexCell(0, 0, 32, {}, None)
def draw_hex():
    glBegin(GL_POLYGON)
    glVertex2f(*cell.topleft)
    glVertex2f(*cell.topright)
    glVertex2f(*cell.right)
    glVertex2f(*cell.bottomright)
    glVertex2f(*cell.bottomleft)
    glVertex2f(*cell.left)
    glEnd()

class HexCheckImage(Drawable):
    COLOURS = [
        (.7, .7, .7, 1),
        (.9, .9, .9, 1),
        (1, 1, 1, 1)
    ]
    def __init__(self, colour, cell):
        Drawable.__init__(self)
        self.colour = colour
        self.cell = cell
        self._style = DrawStyle(color=colour, draw_func=draw_hex)
    def get_drawstyle(self):
        return self._style

def gen_hex_map(meta, h):
    r = []
    cell = None
    for i, m in enumerate(meta):
        c = []
        r.append(c)
        for j, info in enumerate(m):
            if cell is None:
                cell = HexCell(0, 0, h, None, None)
            k = j
            if not i % 2:  k += 1
            image = HexCheckImage(HexCheckImage.COLOURS[k%3], cell)
            c.append(HexCell(i, j, h, dict(info), Tile('dbg', {}, image)))
    return HexMap('debug', h, r)

def gen_rect_map(meta, w, h):
    r = []
    cell = None
    dark = Image2d.from_image(Image.create_solid(w, (150, 150, 150, 255)))
    light = Image2d.from_image(Image.create_solid(w, (200, 200, 200, 255)))
    for i, m in enumerate(meta):
        c = []
        r.append(c)
        for j, info in enumerate(m):
            if (i + j) % 2: image = dark
            else: image = light
            c.append(RectCell(i, j, w, h, dict(info), Tile('dbg', {}, image)))
    return RectMap('debug', w, h, r)

