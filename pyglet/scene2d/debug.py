#!/usr/bin/env python

'''
Simple images etc. to aid debugging
===================================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math

from pyglet.scene2d import *
from pyglet.image import Image
from pyglet.scene2d.drawable import *
from pyglet.GL.VERSION_1_1 import *

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
    def __init__(self, colour, height, padding=0):
        Drawable.__init__(self)
        self.colour = colour
        cell = HexCell(0, 0, height, {}, None)
        padlist = [float(i+1)/(padding+1) for i in range(padding)]
        def draw_hex(style):
            glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ZERO)
            glBegin(GL_LINES)
            x1, y1 = cell.bottomleft
            x2, y2 = cell.left
            w = cell.width
            ly = y2 - y1
            line = brensenham_line(x1, y1, x2, y2)
            mx = max([x for x,y in line])
            r, g, b, a = style.color

            # draw middle wedges
            for i in range(padding):
                a = padlist[i]
                j = padding - i
                glColor4f(r, g, b, a)
                glVertex2f(x2-j, y2 + j)
                glVertex2f(x2-j, y2 - j)
                glVertex2f(w+j-1, y2 + j)
                glVertex2f(w+j-1, y2 - j)

            # draw top
            for x,y in line:
                for i, a in enumerate(padlist):
                    i = padding-i
                    glColor4f(r, g, b, a)
                    glVertex2f(mx-x-i, y + height/2 + i)
                    glVertex2f(w-mx+x+i, y + height/2 + i)

            # draw bottom (reversed so we don't draw over ourselves
            for x,y in reversed(line):
                for i, a in enumerate(padlist):
                    i = padding-i
                    glColor4f(r, g, b, a)
                    glVertex2f(x-i, y - i)
                    glVertex2f(w-x+i, y - i)

            # draw solid (not chewey) center
            for x,y in line:
                glColor4f(*style.color)
                glVertex2f(x, y)
                glVertex2f(w-x, y)
                if x:
                    glVertex2f(mx-x, y + height/2)
                    glVertex2f(w-mx+x, y + height/2)
            glEnd()
            glPopAttrib()
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


def gen_recthex_map(meta, h, padding=0):
    r = []
    cell = None
    image = HexCheckImage((1., 1., 1., 1.), h, padding)
    w = int(h / math.sqrt(3)) * 2
    if padding:
        offset = (padding,padding)
    else:
        offset = None
    for i, m in enumerate(meta):
        c = []
        r.append(c)
        for j, info in enumerate(m):
            c.append(RectCell(i, j, w+padding*2, h+padding*2, dict(info),
                Tile('dbg', {}, image, offset=offset)))
    return RectMap('debug', w, h, r)

