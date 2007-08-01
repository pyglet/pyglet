#!/usr/bin/env python

'''
Simple images etc. to aid debugging
===================================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math

from scene2d import *
from pyglet import image
from scene2d.drawable import *
from pyglet.gl import *

def brensenham_line(x, y, x2, y2):
    '''Modified to draw hex sides in HexCheckImage.
    
    Assumes dy > dx, x>x2 and y2>y which is always the case for what it's
    being used for.'''
    coords = []
    dx = abs(x2 - x)
    dy = abs(y2 - y)
    d = (2 * dx) - dy
    for i in range(0, dy):
        coords.append((x, y))
        while d >= 0:
            x -= 1
            d -= (2 * dy)
        y += 1
        d += (2 * dx)
    coords.append((x2,y2))
    return coords

class HexCheckImage(Drawable):
    COLOURS = [
        (.7, .7, .7, 1),
        (.9, .9, .9, 1),
        (1, 1, 1, 1)
    ]
    def __init__(self, colour, height):
        Drawable.__init__(self)
        cell = HexCell(0, 0, height, {}, None)
        def draw_hex(style):
            w = cell.width
            line = brensenham_line(*(cell.bottomleft + cell.left))
            mx = max([x for x,y in line])

            # draw solid (not chewey) center
            glBegin(GL_LINES)
            for x,y in line:
                glVertex2f(x, y)
                glVertex2f(w-x, y)
                if x:
                    glVertex2f(mx-x, y + height/2)
                    glVertex2f(w-mx+x, y + height/2)
            glEnd()
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
            image = HexCheckImage(HexCheckImage.COLOURS[k%3], h)
            c.append(HexCell(i, j, h, dict(info), Tile('dbg', {}, image)))
    return HexMap('debug', h, r)

def gen_rect_map(meta, w, h):
    r = []
    cell = None
    dark = Image2d.from_image(SolidColorImagePattern((150, 150, 150,
        255)).create_image(w, h))
    light = Image2d.from_image(SolidColorImagePattern((200, 200, 200,
        255)).create_image(w, h))
    for i, m in enumerate(meta):
        c = []
        r.append(c)
        for j, info in enumerate(m):
            if (i + j) % 2: image = dark
            else: image = light
            c.append(RectCell(i, j, w, h, dict(info), Tile('dbg', {}, image)))
    return RectMap('debug', w, h, r)


def gen_recthex_map(meta, h):
    r = []
    cell = None
    dark = HexCheckImage((.4, .4, .4, 1), h)
    light = HexCheckImage((.7, .7, .7, 1), h)
    w = int(h / math.sqrt(3)) * 2
    for i, m in enumerate(meta):
        c = []
        r.append(c)
        for j, info in enumerate(m):
            if (i + j) % 2: image = dark
            else: image = light
            c.append(RectCell(i, j, w, h, dict(info), Tile('dbg', {}, image)))
    return RectMap('debug', w, h, r)

