import math

class MapBase(object):

    def get(self, pos=None, px=None):
        ''' Return Tile at tile pos=(x,y) or pixel px=(x,y).
        Return None if out of bounds.'''
        raise NotImplemented()

class Map(MapBase):
    '''
    Attributes:

        (w, h)    -- size of map in tiles
        (tw, th)  -- size of each tile in pixels
        (x, y, z) -- offset of map top left from origin in pixels
        meta      -- array [x][y] of dicts with meta-data
        images    -- array [x][y] of objects with .draw() and
                     optionally .animate(dt)

    Tiles are stored in column-major order with y increasing up,
    allowing [x][y] addressing:
    +---+---+---+
    | d | e | f |
    +---+---+---+
    | a | b | c |
    +---+---+---+
    Thus tiles = [['a', 'd'], ['b', 'e'], ['c', 'f']]
    and tiles[0][1] = 'd'
    '''
    __slots__ = 'pxw pxh tw th x y z meta images'.split()
    def __init__(self, tw, th, origin=(0, 0, 0), meta=None, images=None):
        if meta is None and images is None:
            raise ValueError, 'Either meta or images must be supplied'
        self.tw, self.th = tw, th
        self.x, self.y, self.z = origin
        self.meta = meta
        self.images = images
        l = meta or images
        self.pxw = len(l) * tw
        self.pxh = len(l[1]) * th
 
    def get(self, pos=None, px=None):
        ''' Return Tile at tile pos=(x,y) or pixel px=(x,y).
        Return None if out of bounds.'''
        if pos is not None:
            x, y = pos
        elif px is not None:
            x, y = px
            x /= self.tw
            y /= self.th
        else:
            raise ValueError, 'Either tile or pixel pos must be supplied'
        if x < 0 or y < 0:
            return None
        try:
            meta = self.meta and self.meta[x][y]
            image = self.images and self.images[x][y]
            return Tile(self, x, y, meta, image)
        except IndexError:
            return None

class TileBase(object):
    def __init__(self, map, x, y, meta, image):
        self.map = map
        self.w, self.h = map.tw, map.th
        self.x, self.y = x, y
        self.meta = meta
        self.image = image

    def __repr__(self):
        return '<%s object at 0x%x (%g, %g) meta=%r image=%r>'%(
            self.__class__.__name__, id(self), self.x, self.y, self.meta,
                self.image)

class Tile(TileBase):
    __slots__ = 'map x y w h meta image'.split()

    # ro, side in pixels, y extent
    def get_top(self):
        return (self.y + 1) * self.h
    top = property(get_top)

    # ro, side in pixels, y extent
    def get_bottom(self):
        return self.y * self.h
    bottom = property(get_bottom)

    # ro, in pixels, (x, y)
    def get_center(self):
        return (self.x * self.w + self.w/2, self.y * self.h + self.h/2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        return (self.x * self.w + self.w/2, self.y * self.h)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        return (self.x * self.w + self.w/2, (self.y + 1) * self.h)
    midbottom = property(get_midbottom)

    # ro, side in pixels, x extent
    def get_left(self):
        return self.x * self.w
    left = property(get_left)

    # ro, side in pixels, x extent
    def get_right(self):
        return (self.x + 1) * self.w
    right = property(get_right)

    # ro, corner in pixels, (x, y)
    def get_topleft(self):
        return (self.x * self.w, self.y * self.h)
    topleft = property(get_topleft)

    # ro, corner in pixels, (x, y)
    def get_topright(self):
        return ((self.x + 1) * self.w, self.y * self.h)
    topright = property(get_topright)

    # ro, corner in pixels, (x, y)
    def get_bottomleft(self):
        return (self.x * self.h, (self.y + 1) * self.h)
    bottomleft = property(get_bottomleft)

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        return ((self.x + 1) * self.w, (self.y + 1) * self.h)
    bottomright = property(get_bottomright)

    # ro, mid-point in pixels, (x, y)
    def get_midleft(self):
        return (self.x * self.w, self.y * self.h + self.h/2)
    midleft = property(get_midleft)
 
    # ro, mid-point in pixels, (x, y)
    def get_midright(self):
        return ((self.x + 1) * self.w, self.y * self.h + self.h/2)
    midright = property(get_midright)
 
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    def get_neighbor(self, direction):
        ''' Return my neighbor Tile in the given direction (dx, dy) which
        could be one of self.UP, self.DOWN, self.LEFT or self.RIGHT.

        Return None if out of bounds.
        '''
        dx, dy = direction
        return self.map.get((self.x + dx, self.y + dy))

 
class HexMap(MapBase):
    '''
    Attributes:

        (pxw, pxh)  -- size of map in pixels
        tw, th      -- size of the hexagons in pixels
        edge_length -- length of an edge in pixels
        (x, y, z)   -- offset of map top left from origin in pixels
        meta        -- array [x][y] of dicts with meta-data
        images      -- array [x][y] of objects with .draw() and
                       optionally .animate(dt)

    Hexmaps store their tiles in an offset array, column-major with y
    increasing up, such that a map:
          /d\ /h\
        /b\_/f\_/
        \_/c\_/g\
        /a\_/e\_/
        \_/ \_/ 
    has tiles = [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'h']]
    '''
    __slots__ = 'tw th edge_length left right pxw pxh x y z meta images'.split()
    def __init__(self, th, origin=(0, 0, 0), meta=None, images=None):
        if meta is None and images is None:
            raise ValueError, 'Either meta or images must be supplied'
        self.th = th
        self.x, self.y, self.z = origin
        self.meta = meta
        self.images = images

        # figure some convenience values
        self.edge_length = int(th / math.sqrt(3))
        self.tw = self.edge_length * 2
        self.left = (self.tw/2, th/2)
        self.right = (self.edge_length * 2, th/2)

        # now figure map dimensions
        l = meta or images
        w = len(l); h = len(l[0])
        self.pxw = HexTile(self, w-1, 0, None, None).right[0]
        if w > 1:
            self.pxh = HexTile(self, 1, h-1, None, None).top
        else:
            self.pxh = HexTile(self, 0, h-1, None, None).top
 
    def get(self, pos=None, px=None):
        ''' Return Tile at tile pos=(x,y) or pixel px=(x,y).
        Return None if out of bounds.'''
        if pos is not None:
            x, y = pos
        elif px is not None:
            raise NotImplemented('TODO: translate pixel to tile')
        else:
            raise ValueError, 'Either tile or pixel pos must be supplied'
        if x < 0 or y < 0:
            return None
        try:
            meta = image = None
            if self.meta:
                meta = self.meta[x][y]
                if meta is None: return None
            if self.images:
                image = self.images[x][y]
                if image is None: return None
            return HexTile(self, x, y, meta, image)
        except IndexError:
            return None
 
# Note that we always add below (not subtract) so that we can try to
# avoid accumulation errors due to rounding ints. We do this so
# we can each point at the same position as a neighbor's corresponding
# point.
class HexTile(TileBase):
    __slots__ = 'map x y w h meta image'.split()

    def get_origin(self):
        x = self.x * (self.w / 2 + self.w / 4)
        y = self.y * self.h
        if self.x % 2:
            y += self.h / 2
        return (x, y)

    # ro, side in pixels, y extent
    def get_top(self):
        y = self.get_origin()[1]
        return y + self.h
    top = property(get_top)

    # ro, side in pixels, y extent
    def get_bottom(self):
        return self.get_origin()[1]
    bottom = property(get_bottom)

    # ro, in pixels, (x, y)
    def get_center(self):
        x, y = self.get_origin()
        return (x + self.w / 2, y + self.h / 2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        x, y = self.get_origin()
        return (x + self.w/2, y + self.h)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        x, y = self.get_origin()
        return (x + self.w/2, y)
    midbottom = property(get_midbottom)

    # ro, side in pixels, x extent
    def get_left(self):
        x, y = self.get_origin()
        return (x, y + self.h/2)
    left = property(get_left)

    # ro, side in pixels, x extent
    def get_right(self):
        x, y = self.get_origin()
        return (x + self.w, y + self.h/2)
    right = property(get_right)

    # ro, corner in pixels, (x, y)
    def get_topleft(self):
        x, y = self.get_origin()
        return (x + self.w / 4, y + self.h)
    topleft = property(get_topleft)

    # ro, corner in pixels, (x, y)
    def get_topright(self):
        x, y = self.get_origin()
        return (x + self.w/2 + self.w / 4, y + self.h)
    topright = property(get_topright)

    # ro, corner in pixels, (x, y)
    def get_bottomleft(self):
        x, y = self.get_origin()
        return (x + self.w / 4, y)
    bottomleft = property(get_bottomleft)

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        x, y = self.get_origin()
        return (x + self.w/2 + self.w / 4, y)
    bottomright = property(get_bottomright)

    # ro, middle of side in pixels, (x, y)
    def get_midtopleft(self):
        x, y = self.get_origin()
        return (x + self.w / 8, y + self.h/2 + self.h/4)
    midtopleft = property(get_midtopleft)

    # ro, middle of side in pixels, (x, y)
    def get_midtopright(self):
        x, y = self.get_origin()
        return (x + self.w / 2 + self.w / 4 + self.w / 8,
            y + self.h/2 + self.h/4)
    midtopright = property(get_midtopright)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomleft(self):
        x, y = self.get_origin()
        return (x + self.w / 8, y + self.h/4)
    midbottomleft = property(get_midbottomleft)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomright(self):
        x, y = self.get_origin()
        return (x + self.w / 2 + self.w / 4 + self.w / 8,
            y + self.h/4)
    midbottomright = property(get_midbottomright)

    UP = 'up'
    DOWN = 'down'
    UP_LEFT = 'up left'
    UP_RIGHT = 'up right'
    DOWN_LEFT = 'down left'
    DOWN_RIGHT = 'down right'
    def get_neighbor(self, direction):
        ''' Return my neighbor HexTile in the given direction which
        is one of self.UP, self.DOWN, self.UP_LEFT, self.UP_RIGHT,
        self.DOWN_LEFT or self.DOWN_RIGHT.

        Return None if out of bounds.
        '''
        if direction is self.UP:
            return self.map.get((self.x, self.y + 1))
        elif direction is self.DOWN:
            return self.map.get((self.x, self.y - 1))
        elif direction is self.UP_LEFT:
            if self.x % 2:
                return self.map.get((self.x - 1, self.y + 1))
            else:
                return self.map.get((self.x - 1, self.y))
        elif direction is self.UP_RIGHT:
            if self.x % 2:
                return self.map.get((self.x + 1, self.y + 1))
            else:
                return self.map.get((self.x + 1, self.y))
        elif direction is self.DOWN_LEFT:
            if self.x % 2:
                return self.map.get((self.x - 1, self.y))
            else:
                return self.map.get((self.x - 1, self.y - 1))
        elif direction is self.DOWN_RIGHT:
            if self.x % 2:
                return self.map.get((self.x + 1, self.y))
            else:
                return self.map.get((self.x + 1, self.y - 1))
        else:
            raise ValueError, 'Unknown direction %r'%direction
