#!/usr/bin/env python

'''
Model code for managing rectangular and hexagonal maps
======================================================

This module provides classes for managing rectangular and hexagonal maps.

---------------
Getting Started
---------------

You may create a map interactively and query it:

TBD

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import math
import xml.dom
import xml.dom.minidom

from resource import Resource, register_factory
from scene2d.drawable import *

@register_factory('rectmap')
def rectmap_factory(resource, tag):
    width, height = map(int, tag.getAttribute('tile_size').split('x'))
    origin = None
    if tag.hasAttribute('origin'):
        origin = map(int, tag.getAttribute('origin').split(','))
    id = tag.getAttribute('id')

    # now load the columns
    cells = []
    for i, column in enumerate(tag.getElementsByTagName('column')):
        c = []
        cells.append(c)
        for j, cell in enumerate(column.getElementsByTagName('cell')):
            tile = cell.getAttribute('tile')
            if tile: tile = resource.get_resource(tile)
            else: tile = None
            properties = resource.handle_properties(cell)
            c.append(RectCell(i, j, width, height, properties, tile))

    m = RectMap(id, width, height, cells, origin)
    resource.add_resource(id, m)

    return m

@register_factory('hexmap')
def hexmap_factory(resource, tag):
    height = int(tag.getAttribute('tile_height'))
    width = hex_width(height)
    origin = None
    if tag.hasAttribute('origin'):
        origin = map(int, tag.getAttribute('origin').split(','))
    id = tag.getAttribute('id')

    # now load the columns
    cells = []
    for i, column in enumerate(tag.getElementsByTagName('column')):
        c = []
        cells.append(c)
        for j, cell in enumerate(column.getElementsByTagName('cell')):
            tile = cell.getAttribute('tile')
            if tile: tile = resource.get_resource(tile)
            else: tile = None
            properties = resource.handle_properties(tag)
            c.append(HexCell(i, j, height, properties, tile))

    m = HexMap(id, width, cells, origin)
    resource.add_resource(id, m)

    return m

def hex_width(height):
    '''Determine a regular hexagon's width given its height.
    '''
    return int(height / math.sqrt(3)) * 2

class Map(object):
    '''Base class for Maps.

    Both rect and hex maps have the following attributes:

        id              -- identifies the map in XML and Resources
        (width, height) -- size of map in cells
        (pxw, pxh)      -- size of map in pixels
        (tw, th)        -- size of each cell in pixels
        (x, y, z)       -- offset of map top left from origin in pixels
        cells           -- array [x][y] of Cell instances
    '''

class RegularTesselationMap(Map):
    '''A class of Map that has a regular array of Cells.
    '''
    def get_cell(self, x, y):
        ''' Return Cell at cell pos=(x,y).

        Return None if out of bounds.'''
        if x < 0 or y < 0:
            return None
        try:
            return self.cells[x][y]
        except IndexError:
            return None

class RectMap(RegularTesselationMap):
    '''Rectangular map.

    Cells are stored in column-major order with y increasing up,
    allowing [x][y] addressing:
    +---+---+---+
    | d | e | f |
    +---+---+---+
    | a | b | c |
    +---+---+---+
    Thus cells = [['a', 'd'], ['b', 'e'], ['c', 'f']]
    and cells[0][1] = 'd'
    '''
    def __init__(self, id, tw, th, cells, origin=None):
        self.id = id
        self.tw, self.th = tw, th
        if origin is None:
            origin = (0, 0, 0)
        self.x, self.y, self.z = origin
        self.cells = cells
        self.pxw = len(cells) * tw
        self.pxh = len(cells[0]) * th

    def get_in_region(self, x1, y1, x2, y2):
        '''Return cells (in [column][row]) that are within the
        pixel bounds specified by the bottom-left (x1, y1) and top-right
        (x2, y2) corners.

        '''
        x1 = max(0, x1 // self.tw)
        y1 = max(0, y1 // self.th)
        x2 = min(len(self.cells), x2 // self.tw + 1)
        y2 = min(len(self.cells[0]), y2 // self.th + 1)
        return [self.cells[x][y] for x in range(x1, x2) for y in range(y1, y2)]
 
    def get(self, x, y):
        ''' Return Cell at pixel px=(x,y).

        Return None if out of bounds.'''
        return self.get_cell(x // self.tw, y // self.th)
 
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    def get_neighbor(self, cell, direction):
        '''Get the neighbor Cell in the given direction (dx, dy) which
        is one of self.UP, self.DOWN, self.LEFT or self.RIGHT.

        Returns None if out of bounds.
        '''
        dx, dy = direction
        return self.get_cell(cell.x + dx, cell.y + dy)

    @classmethod
    def load_xml(cls, filename, id):
        '''Load a map from the indicated XML file.

        Return a Map instance.'''
        return Resource.load(filename)[id]

class Cell(Drawable):
    '''Base class for cells from rect and hex maps.

    Common attributes:
        x, y        -- top-left coordinate
        width, height        -- dimensions
        properties        -- arbitrary properties
        cell       -- cell from the Map's cells
    '''
    def __init__(self, x, y, width, height, properties, tile):
        super(Cell, self).__init__()
        self.width, self.height = width, height
        self.x, self.y = x, y
        self.properties = properties
        self.tile = tile

        if tile is not None:
            # pre-calculate the style to force creation of _style
            self.get_style()

    def __repr__(self):
        return '<%s object at 0x%x (%g, %g) properties=%r tile=%r>'%(
            self.__class__.__name__, id(self), self.x, self.y,
                self.properties, self.tile)

    def get_style(self):
        if self.tile is None: return None
        return super(Cell, self).get_style()

    def get_drawstyle(self):
        '''Get the possibly-affected style from the tile. Adjust for this
        cell's position.
        '''
        style = self.tile.get_style().copy()
        x, y = self.get_origin()
        style.x, style.y = style.x + x, style.y + y
        return style

class RectCell(Cell):
    '''A rectangular cell from a Map.

    Read-only attributes:
        top         -- y extent
        bottom      -- y extent
        left        -- x extent
        right       -- x extent
        origin      -- (x, y) of bottom-left corner
        center      -- (x, y)
        topleft     -- (x, y) of top-left corner
        topright    -- (x, y) of top-right corner
        bottomleft  -- (x, y) of bottom-left corner
        bottomright -- (x, y) of bottom-right corner
        midtop      -- (x, y) of middle of top side
        midbottom   -- (x, y) of middle of bottom side
        midleft     -- (x, y) of middle of left side
        midright    -- (x, y) of middle of right side
    '''
    def get_origin(self):
        return self.x * self.width, self.y * self.height
    origin = property(get_origin)

    # ro, side in pixels, y extent
    def get_top(self):
        return (self.y + 1) * self.height
    top = property(get_top)

    # ro, side in pixels, y extent
    def get_bottom(self):
        return self.y * self.height
    bottom = property(get_bottom)

    # ro, in pixels, (x, y)
    def get_center(self):
        return (self.x * self.width + self.width // 2,
            self.y * self.height + self.height // 2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        return (self.x * self.width + self.width // 2,
            (self.y + 1) * self.height)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        return (self.x * self.width + self.width // 2, self.y * self.height)
    midbottom = property(get_midbottom)

    # ro, side in pixels, x extent
    def get_left(self):
        return self.x * self.width
    left = property(get_left)

    # ro, side in pixels, x extent
    def get_right(self):
        return (self.x + 1) * self.width
    right = property(get_right)

    # ro, corner in pixels, (x, y)
    def get_topleft(self):
        return (self.x * self.width, (self.y + 1) * self.height)
    topleft = property(get_topleft)

    # ro, corner in pixels, (x, y)
    def get_topright(self):
        return ((self.x + 1) * self.width, (self.y + 1) * self.height)
    topright = property(get_topright)

    # ro, corner in pixels, (x, y)
    def get_bottomleft(self):
        return (self.x * self.height, self.y * self.height)
    bottomleft = property(get_bottomleft)
    origin = property(get_bottomleft)

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        return ((self.x + 1) * self.width, self.y * self.height)
    bottomright = property(get_bottomright)

    # ro, mid-point in pixels, (x, y)
    def get_midleft(self):
        return (self.x * self.width, self.y * self.height + self.height // 2)
    midleft = property(get_midleft)
 
    # ro, mid-point in pixels, (x, y)
    def get_midright(self):
        return ((self.x + 1) * self.width,
            self.y * self.height + self.height // 2)
    midright = property(get_midright)

 
class HexMap(RegularTesselationMap):
    '''Map with flat-top, regular hexagonal cells.

    Additional attributes extending MapBase:

        edge_length -- length of an edge in pixels

    Hexmaps store their cells in an offset array, column-major with y
    increasing up, such that a map:
          /d\ /h\
        /b\_/f\_/
        \_/c\_/g\
        /a\_/e\_/
        \_/ \_/ 
    has cells = [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'h']]
    '''
    def __init__(self, id, th, cells, origin=None):
        self.id = id
        self.th = th
        if origin is None:
            origin = (0, 0, 0)
        self.x, self.y, self.z = origin
        self.cells = cells

        # figure some convenience values
        s = self.edge_length = int(th / math.sqrt(3))
        self.tw = self.edge_length * 2

        # now figure map dimensions
        width = len(cells); height = len(cells[0])
        self.pxw = self.tw + (width - 1) * (s + s // 2)
        self.pxh = height * self.th
        if not width % 2:
            self.pxh += (th // 2)

    def get_in_region(self, x1, y1, x2, y2):
        '''Return cells (in [column][row]) that are within the pixel bounds
        specified by the bottom-left (x1, y1) and top-right (x2, y2) corners.
        '''
        col_width = self.tw // 2 + self.tw // 4
        x1 = max(0, x1 // col_width)
        y1 = max(0, y1 // self.th - 1)
        x2 = min(len(self.cells), x2 // col_width + 1)
        y2 = min(len(self.cells[0]), y2 // self.th + 1)
        return [self.cells[x][y] for x in range(x1, x2) for y in range(y1, y2)]
 
    def get(self, x, y):
        '''Get the Cell at pixel px=(x,y).
        Return None if out of bounds.'''
        s = self.edge_length
        # map is divided into columns of
        # s/2 (shared), s, s/2(shared), s, s/2 (shared), ...
        x = x // (s/2 + s)
        if x % 2:
            # every second cell is up one
            y -= self.th // 2
        y = y // self.th
        return self.get_cell(x, y)

    UP = 'up'
    DOWN = 'down'
    UP_LEFT = 'up left'
    UP_RIGHT = 'up right'
    DOWN_LEFT = 'down left'
    DOWN_RIGHT = 'down right'
    def get_neighbor(self, cell, direction):
        '''Get the neighbor HexCell in the given direction which
        is one of self.UP, self.DOWN, self.UP_LEFT, self.UP_RIGHT,
        self.DOWN_LEFT or self.DOWN_RIGHT.

        Return None if out of bounds.
        '''
        if direction is self.UP:
            return self.get_cell(cell.x, cell.y + 1)
        elif direction is self.DOWN:
            return self.get_cell(cell.x, cell.y - 1)
        elif direction is self.UP_LEFT:
            if cell.x % 2:
                return self.get_cell(cell.x - 1, cell.y + 1)
            else:
                return self.get_cell(cell.x - 1, cell.y)
        elif direction is self.UP_RIGHT:
            if cell.x % 2:
                return self.get_cell(cell.x + 1, cell.y + 1)
            else:
                return self.get_cell(cell.x + 1, cell.y)
        elif direction is self.DOWN_LEFT:
            if cell.x % 2:
                return self.get_cell(cell.x - 1, cell.y)
            else:
                return self.get_cell(cell.x - 1, cell.y - 1)
        elif direction is self.DOWN_RIGHT:
            if cell.x % 2:
                return self.get_cell(cell.x + 1, cell.y)
            else:
                return self.get_cell(cell.x + 1, cell.y - 1)
        else:
            raise ValueError, 'Unknown direction %r'%direction
 
# Note that we always add below (not subtract) so that we can try to
# avoid accumulation errors due to rounding ints. We do this so
# we can each point at the same position as a neighbor's corresponding
# point.
class HexCell(Cell):
    '''A flat-top, regular hexagon cell from a HexMap.

    Read-only attributes:
        top             -- y extent
        bottom          -- y extent
        left            -- (x, y) of left corner
        right           -- (x, y) of right corner
        center          -- (x, y)
        origin          -- (x, y) of bottom-left corner of bounding rect
        topleft         -- (x, y) of top-left corner
        topright        -- (x, y) of top-right corner
        bottomleft      -- (x, y) of bottom-left corner
        bottomright     -- (x, y) of bottom-right corner
        midtop          -- (x, y) of middle of top side
        midbottom       -- (x, y) of middle of bottom side
        midtopleft      -- (x, y) of middle of left side
        midtopright     -- (x, y) of middle of right side
        midbottomleft   -- (x, y) of middle of left side
        midbottomright  -- (x, y) of middle of right side
    '''
    def __init__(self, x, y, height, properties, tile):
        width = hex_width(height)
        Cell.__init__(self, x, y, width, height, properties, tile)

    def get_origin(self):
        x = self.x * (self.width / 2 + self.width // 4)
        y = self.y * self.height
        if self.x % 2:
            y += self.height // 2
        return (x, y)
    origin = property(get_origin)

    # ro, side in pixels, y extent
    def get_top(self):
        y = self.get_origin()[1]
        return y + self.height
    top = property(get_top)

    # ro, side in pixels, y extent
    def get_bottom(self):
        return self.get_origin()[1]
    bottom = property(get_bottom)

    # ro, in pixels, (x, y)
    def get_center(self):
        x, y = self.get_origin()
        return (x + self.width // 2, y + self.height // 2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        x, y = self.get_origin()
        return (x + self.width // 2, y + self.height)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        x, y = self.get_origin()
        return (x + self.width // 2, y)
    midbottom = property(get_midbottom)

    # ro, side in pixels, x extent
    def get_left(self):
        x, y = self.get_origin()
        return (x, y + self.height // 2)
    left = property(get_left)

    # ro, side in pixels, x extent
    def get_right(self):
        x, y = self.get_origin()
        return (x + self.width, y + self.height // 2)
    right = property(get_right)

    # ro, corner in pixels, (x, y)
    def get_topleft(self):
        x, y = self.get_origin()
        return (x + self.width // 4, y + self.height)
    topleft = property(get_topleft)

    # ro, corner in pixels, (x, y)
    def get_topright(self):
        x, y = self.get_origin()
        return (x + self.width // 2 + self.width // 4, y + self.height)
    topright = property(get_topright)

    # ro, corner in pixels, (x, y)
    def get_bottomleft(self):
        x, y = self.get_origin()
        return (x + self.width // 4, y)
    bottomleft = property(get_bottomleft)

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        x, y = self.get_origin()
        return (x + self.width // 2 + self.width // 4, y)
    bottomright = property(get_bottomright)

    # ro, middle of side in pixels, (x, y)
    def get_midtopleft(self):
        x, y = self.get_origin()
        return (x + self.width // 8, y + self.height // 2 + self.height // 4)
    midtopleft = property(get_midtopleft)

    # ro, middle of side in pixels, (x, y)
    def get_midtopright(self):
        x, y = self.get_origin()
        return (x + self.width // 2 + self.width // 4 + self.width // 8,
            y + self.height // 2 + self.height // 4)
    midtopright = property(get_midtopright)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomleft(self):
        x, y = self.get_origin()
        return (x + self.width // 8, y + self.height // 4)
    midbottomleft = property(get_midbottomleft)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomright(self):
        x, y = self.get_origin()
        return (x + self.width // 2 + self.width // 4 + self.width // 8,
            y + self.height // 4)
    midbottomright = property(get_midbottomright)

