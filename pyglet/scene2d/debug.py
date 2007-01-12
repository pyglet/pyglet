#!/usr/bin/env python

'''
Simple images etc. to aid debugging
===================================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.scene2d.map import RectMap, HexMap, RectCell, HexCell
from pyglet.scene2d.tile import Tile
from pyglet.GL.VERSION_1_1 import *

class HexCheckImage:
    COLOURS = [
        (.7, .7, .7, 1),
        (.9, .9, .9, 1),
        (1, 1, 1, 1)
    ]
    def __init__(self, colour, cell):
        self.colour = colour
        self.cell = cell
    def draw(self):
        glColor4f(*self.colour)
        glBegin(GL_POLYGON)
        glVertex2f(*self.cell.topleft)
        glVertex2f(*self.cell.topright)
        glVertex2f(*self.cell.right)
        glVertex2f(*self.cell.bottomright)
        glVertex2f(*self.cell.bottomleft)
        glVertex2f(*self.cell.left)
        glEnd()

class RectCheckImage:
    def __init__(self, w, h, colour):
        self.w, self.h = w, h
        self.colour = colour
    def draw(self):
        glColor4f(*self.colour)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.w, 0)
        glVertex2f(self.w, self.h)
        glVertex2f(0, self.h)
        glEnd()

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
            c.append(HexCell(i, j, h, info, Tile('dbg', {}, image)))
    return HexMap('debug', h, r)

def gen_rect_map(meta, w, h):
    r = []
    cell = None
    for i, m in enumerate(meta):
        c = []
        r.append(c)
        for j, info in enumerate(m):
            if (i + j) % 2:
                image = RectCheckImage(w, h, (.7, .7, .7, 1))
            else:
                image = RectCheckImage(w, h, (.9, .9, .9, 1))
            c.append(RectCell(i, j, w, h, info, Tile('dbg', {}, image)))
    return RectMap('debug', w, h, r)

