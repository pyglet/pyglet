#!/usr/bin/env python

'''
Simple images etc. to aid debugging
===================================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.scene2d.map import HexCell, Tile
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

def genmap(meta, w, h, klass):
    r = []
    cell = None
    for i, m in enumerate(meta):
        c = []
        r.append(c)
        for j, info in enumerate(m):
            if klass is HexCell:
                if cell is None:
                    cell = HexCell(0, 0, w, h, None, None)
                k = j
                if not i % 2:  k += 1
                image = HexCheckImage(HexCheckImage.COLOURS[k%3], cell)
            else:
                if (i + j) % 2:
                    image = RectCheckImage(w, h, (.7, .7, .7, 1))
                else:
                    image = RectCheckImage(w, h, (.9, .9, .9, 1))
            c.append(klass(i, j, w, h, info, Tile(None, None, image)))
    return r
