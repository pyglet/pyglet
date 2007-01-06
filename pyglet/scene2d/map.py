#!/usr/bin/env python

'''
Model code for managing rectangular and hexagonal maps
======================================================

This module provides classes for managing rectangular and hexagonal maps.

---------------
Getting Started
---------------

You may create a map interactively and query it:

    >>> from pyglet.scene2d import *
    >>> m = RectMap(32, 32, meta=[['a', 'd'], ['b', 'e'], ['c', 'f']])
    >>> m.get((0,0))
    <RectCell object at 0x-4828d82c (0, 0) meta='a' tile=None>
    >>> _.get_neighbor(_.RIGHT)
    <RectCell object at 0x-483c80bc (1, 0) meta='b' tile=None>
    >>> _.get_neighbor(_.UP)
    <RectCell object at 0x-4828d82c (1, 1) meta='e' tile=None>
    >>> print _.get_neighbor(_.UP)
    None

Similarly:

    >>> m = HexMap(32, meta=[['a', 'b'], ['c', 'd'], ['e', 'f']])
    >>> m.get((0,0))
    <HexCell object at 0x-482f682c (0, 0) meta='a' tile=None>
    >>> _.get_neighbor(_.UP)
    <HexCell object at 0x-484310bc (0, 1) meta='b' tile=None>
    >>> _.get_neighbor(_.DOWN_RIGHT)
    <HexCell object at 0x-484310bc (2, 0) meta='e' tile=None>
    >>> print _.get_neighbor(_.DOWN)
    None


----------------
Pyglet Map Files
----------------

There's two files that make up pyglet maps. These correspond to the Tileset
and Map/HexMap above. XML files with the following structure:

<tileset width="" height="">
 <image filename="">
  <tile id="">
   <origin x="" y="" />
   <meta type="" value="" />
  </tile>
  ...
 </image>
 ...
 <tile id="">
  <meta name="" type="" value="" />
 </tile>
 ...
</tileset>

<map tile_width="" tile_height="" x="" y="" z="">
 <tileset id="" filename="" />
 ...
 <column>
  <cell set="" tile="">
   <meta type="" value="" />
  </cell>
  ...
 </column>
 ...
</map>
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import math
import xml.dom
import xml.dom.minidom

from pyglet.scene2d.image import Image2d

class Tile(object):
    __slots__ = 'id meta image'.split()
    def __init__(self, id, meta, image):
        self.id = id
        self.meta = meta
        self.image = image

xml_to_python = {
    'str': str,
    'unicode': unicode,
    'int': int,
    'float': float,
    'bool': bool,
}

class TileSet(dict):
    '''Contains a tile set loaded from a map file and optionally image(s).
    '''
    __slots__ = 'width height'.split()

    # We retain a cache of opened tilesets so that multiple maps may refer to
    # the same tileset and we don't waste resources by duplicating the
    # tilesets in memory.
    tilesets = {}

    tile_id = 0
    @classmethod
    def generate_id(cls):
        cls.tile_id += 1
        return str(cls.tile_id)

    def add(self, meta, image, id=None):
        '''Add a new Tile to this TileSet, generating a unique id if
        necessary.'''
        if id is None:
            id = self.generate_id()
        self[id] = Tile(id, meta, image)

    @classmethod
    def load_xml(cls, filename):
        '''Load the tileset from the XML in the specified file.

        Note that the image tags are optional:

            <tileset width="" height="">
             <image filename="">
              <tile id="">
               <origin x="" y="" />
               <meta name="" type="" value="" />
              </tile>
              ...
             </image>
             ...
             <tile id="">
              <meta name="" type="" value="" />
             </tile>
             ...
            </tileset>
        '''

        if filename in cls.tilesets:
            return cls.tilesets[filename]
        dirname = os.path.dirname(filename)

        dom = xml.dom.minidom.parse(filename)
        tileset = dom.documentElement

        obj = cls()
        obj.width = int(tileset.getAttribute('width'))
        obj.height = int(tileset.getAttribute('height'))
        for child in tileset.childNodes:
            if not hasattr(child, 'tagName'): continue
            if child.tagName == 'image':
                filename = child.getAttribute('filename')
                if not os.path.isabs(filename):
                    filename = os.path.join(dirname, filename)
                image = Image2d.load(filename)

                for child in child.childNodes:
                    if not hasattr(child, 'tagName'): continue
                    id = child.getAttribute('id')
                    origin = child.getElementsByTagName('origin')[0]
                    x, y = map(int, (origin.getAttribute('x'),
                        origin.getAttribute('y')))

                    subimage = image.subimage(x, y, obj.width, obj.height)

                    meta = {}
                    for tag in child.getElementsByTagName('meta'):
                        name = tag.getAttribute('name')
                        type = tag.getAttribute('type')
                        value = tag.getAttribute('value')
                        meta[name] = xml_to_python[type](value)
                    subimage.quad_list
                    obj[id] = Tile(id, meta, subimage)
            else:
                id = child.getAttribute('id')
                meta = {}
                for tag in child.getElementsByTagName('meta'):
                    name = tag.getAttribute('name')
                    type = tag.getAttribute('type')
                    value = tag.getAttribute('value')
                    meta[name] = xml_to_python[type](value)
                obj[id] = Tile(id, meta, None)
        dom.unlink()
        cls.tilesets[filename] = obj
        return obj

class Map(object):
    '''Base class for Maps.

    Both rect and hex maps have the following attributes:

        (width, height) -- size of map in cells
        (pxw, pxh)      -- size of map in pixels
        (tw, th)        -- size of each cell in pixels
        (x, y, z)       -- offset of map top left from origin in pixels
        meta            -- array [x][y] of meta-data (arbitrary data allowed)
        cells           -- array [x][y] of objects with .draw() and
                           optionally .animate(dt)
    '''
    def get(self, pos=None, px=None):
        ''' Return Cell at cell pos=(x,y) or pixel px=(x,y).
        Return None if out of bounds.'''
        raise NotImplemented()

class RectMap(Map):
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
    __slots__ = 'pxw pxh tw th x y z meta cells'.split()
    def __init__(self, tw, th, cells, origin=(0, 0, 0)):
        self.tw, self.th = tw, th
        self.x, self.y, self.z = origin
        self.cells = cells
        self.pxw = len(cells) * tw
        self.pxh = len(cells[1]) * th
 
    def get(self, pos=None, px=None):
        ''' Return Cell at cell pos=(x,y) or pixel px=(x,y).

        Return None if out of bounds.'''
        if pos is not None:
            x, y = pos
        elif px is not None:
            x, y = px
            x /= self.tw
            y /= self.th
        else:
            raise ValueError, 'Either cell or pixel pos must be supplied'
        if x < 0 or y < 0:
            return None
        try:
            return self.cells[x][y]
        except IndexError:
            return None
 
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
        return self.get((cell.x + dx, cell.y + dy))

    @classmethod
    def load_xml(cls, filename):
        '''Load a map from the indicaed XML file.

        The XML format is:

            <map tile_width="" tile_height="" x="" y="" z="">
             <tileset id="" filename="" />
             ...
             <column>
              <cell set="" tile="">
               <meta type="" value="" />
              </cell>
              ...
             </column>
             ...
            </map>
        
        Return a Map instance.'''

        dom = xml.dom.minidom.parse(filename)
        dirname = os.path.dirname(filename)
        map = dom.documentElement

        width = int(map.getAttribute('tile_width'))
        height = int(map.getAttribute('tile_height'))
        origin = (int(map.getAttribute('x')),
            int(map.getAttribute('y')), int(map.getAttribute('z')))

        # load all the tilesets
        tilesets = {}
        for tileset in map.getElementsByTagName('tileset'):
            id = tileset.getAttribute('id')
            filename = tileset.getAttribute('filename')
            if not os.path.isabs(filename):
                filename = os.path.join(dirname, filename)
            tilesets[id] = TileSet.load_xml(filename)

        # now load the columns
        cells = []
        for i, column in enumerate(map.getElementsByTagName('column')):
            c = []
            cells.append(c)
            for j, cell in enumerate(column.getElementsByTagName('cell')):
                if cell.hasAttribute('set'):
                    tileset = cell.getAttribute('set')
                    tile = cell.getAttribute('tile')
                    tile = tilesets[tileset][tile]
                else:
                    tile = None
                meta = {}
                for tag in cell.getElementsByTagName('meta'):
                    name = tag.getAttribute('name')
                    type = tag.getAttribute('type')
                    value = tag.getAttribute('value')
                    meta[name] = xml_to_python[type](value)
                c.append(RectCell(i, j, width, height, meta, tile))

        dom.unlink()
        obj = cls(width, height, cells, origin)
        return obj

class Cell(object):
    '''Base class for cells from rect and hex maps.

    Common attributes:
        x, y        -- top-left coordinate
        width, height        -- dimensions
        meta        -- meta-data from the Map's meta
        cell       -- cell from the Map's cells
    '''
    def __init__(self, x, y, width, height, meta, tile):
        self.width, self.height = width, height
        self.x, self.y = x, y
        self.meta = meta
        self.tile = tile

    def __repr__(self):
        return '<%s object at 0x%x (%g, %g) meta=%r tile=%r>'%(
            self.__class__.__name__, id(self), self.x, self.y, self.meta,
                self.tile)

class RectCell(Cell):
    '''A rectangular cell from a Map.

    Read-only attributes:
        top         -- y extent
        bottom      -- y extent
        left        -- x extent
        right       -- x extent
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
    __slots__ = 'map x y width height meta tile'.split()

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
        return (self.x * self.width + self.width/2, self.y * self.height + self.height/2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        return (self.x * self.width + self.width/2, (self.y + 1) * self.height)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        return (self.x * self.width + self.width/2, self.y * self.height)
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

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        return ((self.x + 1) * self.width, self.y * self.height)
    bottomright = property(get_bottomright)

    # ro, mid-point in pixels, (x, y)
    def get_midleft(self):
        return (self.x * self.width, self.y * self.height + self.height/2)
    midleft = property(get_midleft)
 
    # ro, mid-point in pixels, (x, y)
    def get_midright(self):
        return ((self.x + 1) * self.width, self.y * self.height + self.height/2)
    midright = property(get_midright)

 
class HexMap(Map):
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
    __slots__ = 'tw th edge_length left right pxw pxh x y z meta cells'.split()
    def __init__(self, th, cells, origin=(0, 0, 0)):
        self.th = th
        self.x, self.y, self.z = origin
        self.cells = cells

        # figure some convenience values
        self.edge_length = int(th / math.sqrt(3))
        self.tw = self.edge_length * 2
        self.left = (self.tw/2, th/2)
        self.right = (self.edge_length * 2, th/2)

        # now figure map dimensions
        width = len(cells); height = len(cells[0])
        self.pxw = HexCell(width-1, 0, self.tw, self.th, None, None).right[0]
        if width > 1:
            self.pxh = HexCell(1, height-1, self.tw, self.th, None, None).top
        else:
            self.pxh = HexCell(0, height-1, self.tw, self.th, None, None).top
 
    def get(self, pos=None, px=None):
        '''Get the Cell at cell pos=(x,y) or pixel px=(x,y).

        Return None if out of bounds.'''
        if pos is not None:
            x, y = pos
        elif px is not None:
            raise NotImplemented('TODO: translate pixel to cell')
        else:
            raise ValueError, 'Either cell or pixel pos must be supplied'
        if x < 0 or y < 0:
            return None
        try:
            return self.cells[x][y]
        except IndexError:
            return None

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
            return self.get((cell.x, cell.y + 1))
        elif direction is self.DOWN:
            return self.get((cell.x, cell.y - 1))
        elif direction is self.UP_LEFT:
            if cell.x % 2:
                return self.get((cell.x - 1, cell.y + 1))
            else:
                return self.get((cell.x - 1, cell.y))
        elif direction is self.UP_RIGHT:
            if cell.x % 2:
                return self.get((cell.x + 1, cell.y + 1))
            else:
                return self.get((cell.x + 1, cell.y))
        elif direction is self.DOWN_LEFT:
            if cell.x % 2:
                return self.get((cell.x - 1, cell.y))
            else:
                return self.get((cell.x - 1, cell.y - 1))
        elif direction is self.DOWN_RIGHT:
            if cell.x % 2:
                return self.get((cell.x + 1, cell.y))
            else:
                return self.get((cell.x + 1, cell.y - 1))
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
    __slots__ = 'map x y width height meta tile'.split()

    def get_origin(self):
        x = self.x * (self.width / 2 + self.width / 4)
        y = self.y * self.height
        if self.x % 2:
            y += self.height / 2
        return (x, y)

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
        return (x + self.width / 2, y + self.height / 2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        x, y = self.get_origin()
        return (x + self.width/2, y + self.height)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        x, y = self.get_origin()
        return (x + self.width/2, y)
    midbottom = property(get_midbottom)

    # ro, side in pixels, x extent
    def get_left(self):
        x, y = self.get_origin()
        return (x, y + self.height/2)
    left = property(get_left)

    # ro, side in pixels, x extent
    def get_right(self):
        x, y = self.get_origin()
        return (x + self.width, y + self.height/2)
    right = property(get_right)

    # ro, corner in pixels, (x, y)
    def get_topleft(self):
        x, y = self.get_origin()
        return (x + self.width / 4, y + self.height)
    topleft = property(get_topleft)

    # ro, corner in pixels, (x, y)
    def get_topright(self):
        x, y = self.get_origin()
        return (x + self.width/2 + self.width / 4, y + self.height)
    topright = property(get_topright)

    # ro, corner in pixels, (x, y)
    def get_bottomleft(self):
        x, y = self.get_origin()
        return (x + self.width / 4, y)
    bottomleft = property(get_bottomleft)

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        x, y = self.get_origin()
        return (x + self.width/2 + self.width / 4, y)
    bottomright = property(get_bottomright)

    # ro, middle of side in pixels, (x, y)
    def get_midtopleft(self):
        x, y = self.get_origin()
        return (x + self.width / 8, y + self.height/2 + self.height/4)
    midtopleft = property(get_midtopleft)

    # ro, middle of side in pixels, (x, y)
    def get_midtopright(self):
        x, y = self.get_origin()
        return (x + self.width / 2 + self.width / 4 + self.width / 8,
            y + self.height/2 + self.height/4)
    midtopright = property(get_midtopright)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomleft(self):
        x, y = self.get_origin()
        return (x + self.width / 8, y + self.height/4)
    midbottomleft = property(get_midbottomleft)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomright(self):
        x, y = self.get_origin()
        return (x + self.width / 2 + self.width / 4 + self.width / 8,
            y + self.height/4)
    midbottomright = property(get_midbottomright)

