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
        /f\_/g\_/h\
        \_/d\_/e\_/
        /a\_/b\_/c\
        \_/ \_/ \_/
    has tiles = [['a', 'd', 'f'], ['b', 'e', 'g'], ['c', None, 'h']]

    BTW, hex interior angle = 120 degrees.
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
        if h > 1:
            self.pxw = HexTile(self, w-1, 1, None, None).right[0]
        else:
            self.pxw = HexTile(self, w-1, 0, None, None).right[0]
        self.pxh = HexTile(self, w-1, h-1, None, None).top
 
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
        x = self.x * (self.w + self.w / 2)
        y = (self.y / 2) * self.h
        if self.y % 2:
            y += self.h / 2
            x += self.w / 2 + self.w / 4
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
        dx = dy = 0
        if direction is self.UP:
            dy = 2
        elif direction is self.DOWN:
            dy = -2
        elif direction is self.UP_LEFT:
            dy = 1
            if not self.y % 2: dx = -1
        elif direction is self.UP_RIGHT:
            dy = 1
            if self.y % 2: dx = 1
        elif direction is self.DOWN_LEFT:
            dy = -1
            if not self.y % 2: dx = -1
        elif direction is self.DOWN_RIGHT:
            dy = -1
            if self.y % 2: dx = 1
        return self.map.get((self.x + dx, self.y + dy))


if __name__ == '__main__':
    # test rectangular tile map
    #    +---+---+---+
    #    | d | e | f |
    #    +---+---+---+
    #    | a | b | c |
    #    +---+---+---+
    m = Map(10, 16, meta=[['a', 'd'], ['b', 'e'], ['c', 'f']])
    t = m.get((0,0))
    assert (t.x, t.y) == (0, 0) and t.meta == 'a'
    assert t.get_neighbor(t.UP) is None
    assert t.get_neighbor(t.DOWN).meta == 'd'
    assert t.get_neighbor(t.LEFT) is None
    assert t.get_neighbor(t.RIGHT).meta == 'b'
    t = t.get_neighbor(t.DOWN)
    assert (t.x, t.y) == (0, 1) and t.meta == 'd'
    assert t.get_neighbor(t.UP).meta == 'a'
    assert t.get_neighbor(t.DOWN) is None
    assert t.get_neighbor(t.LEFT) is None
    assert t.get_neighbor(t.RIGHT).meta == 'e'
    t = t.get_neighbor(t.RIGHT)
    assert (t.x, t.y) == (1, 1) and t.meta == 'e'
    assert t.get_neighbor(t.UP).meta == 'b'
    assert t.get_neighbor(t.DOWN) is None
    assert t.get_neighbor(t.RIGHT).meta == 'f'
    assert t.get_neighbor(t.LEFT).meta == 'd'
    t = t.get_neighbor(t.RIGHT)
    assert (t.x, t.y) == (2, 1) and t.meta == 'f'
    assert t.get_neighbor(t.UP).meta == 'c'
    assert t.get_neighbor(t.DOWN) is None
    assert t.get_neighbor(t.RIGHT) is None
    assert t.get_neighbor(t.LEFT).meta == 'e'
    t = t.get_neighbor(t.UP)
    assert (t.x, t.y) == (2, 0) and t.meta == 'c'
    assert t.get_neighbor(t.UP) is None
    assert t.get_neighbor(t.DOWN).meta == 'f'
    assert t.get_neighbor(t.RIGHT) is None
    assert t.get_neighbor(t.LEFT).meta == 'b'

    # test tile sides / corners
    t = m.get((0,0))
    assert t.top == 16
    assert t.bottom == 0
    assert t.left == 0
    assert t.right == 10
    assert t.topleft == (0, 0)
    assert t.topright == (10, 0)
    assert t.bottomleft == (0, 16)
    assert t.bottomright == (10, 16)
    assert t.midtop == (5, 0)
    assert t.midleft == (0, 8)
    assert t.midright == (10, 8)
    assert t.midbottom == (5, 16)

    # test hexagonal tile map
    #   /f\_/g\_/h\
    #   \_/d\_/e\_/
    #   /a\_/b\_/c\
    #   \_/ \_/ \_/
    m = HexMap(32, meta=[['a', 'd', 'f'], ['b', 'e', 'g'], ['c', None, 'h']])
    t = m.get((0,0))
    assert (t.x, t.y) == (0, 0) and t.meta == 'a'
    assert t.get_neighbor(t.DOWN) is None
    assert t.get_neighbor(t.UP).meta == 'f'
    assert t.get_neighbor(t.DOWN_LEFT) is None
    assert t.get_neighbor(t.DOWN_RIGHT) is None
    assert t.get_neighbor(t.UP_LEFT) is None
    assert t.get_neighbor(t.UP_RIGHT).meta == 'd'
    t = t.get_neighbor(t.UP)
    assert (t.x, t.y) == (0, 2) and t.meta == 'f'
    assert t.get_neighbor(t.DOWN).meta == 'a'
    assert t.get_neighbor(t.UP) is None
    assert t.get_neighbor(t.DOWN_LEFT) is None
    assert t.get_neighbor(t.DOWN_RIGHT).meta == 'd'
    assert t.get_neighbor(t.UP_LEFT) is None
    assert t.get_neighbor(t.UP_RIGHT) is None
    t = t.get_neighbor(t.DOWN_RIGHT)
    assert (t.x, t.y) == (0, 1) and t.meta == 'd'
    assert t.get_neighbor(t.DOWN) is None
    assert t.get_neighbor(t.UP) is None
    assert t.get_neighbor(t.DOWN_LEFT).meta == 'a'
    assert t.get_neighbor(t.DOWN_RIGHT).meta == 'b'
    assert t.get_neighbor(t.UP_LEFT).meta == 'f'
    assert t.get_neighbor(t.UP_RIGHT).meta == 'g'
    t = t.get_neighbor(t.UP_RIGHT)
    assert (t.x, t.y) == (1, 2) and t.meta == 'g'
    assert t.get_neighbor(t.DOWN).meta == 'b'
    assert t.get_neighbor(t.UP) is None
    assert t.get_neighbor(t.DOWN_LEFT).meta == 'd'
    assert t.get_neighbor(t.DOWN_RIGHT).meta == 'e'
    assert t.get_neighbor(t.UP_LEFT) is None
    assert t.get_neighbor(t.UP_RIGHT) is None
    t = t.get_neighbor(t.DOWN_RIGHT)
    t = t.get_neighbor(t.DOWN_RIGHT)
    assert (t.x, t.y) == (2, 0) and t.meta == 'c'
    assert t.get_neighbor(t.DOWN) is None
    assert t.get_neighbor(t.UP).meta == 'h'
    assert t.get_neighbor(t.DOWN_LEFT) is None
    assert t.get_neighbor(t.DOWN_RIGHT) is None
    assert t.get_neighbor(t.UP_LEFT).meta == 'e'
    assert t.get_neighbor(t.UP_RIGHT) is None
    t = t.get_neighbor(t.UP)
    assert (t.x, t.y) == (2, 2) and t.meta == 'h'
    assert t.get_neighbor(t.DOWN).meta == 'c'
    assert t.get_neighbor(t.UP) is None
    assert t.get_neighbor(t.DOWN_LEFT).meta == 'e'
    assert t.get_neighbor(t.DOWN_RIGHT) is None
    assert t.get_neighbor(t.UP_LEFT) is None
    assert t.get_neighbor(t.UP_RIGHT) is None

    # test tile sides / corners
    t00 = m.get((0, 0))
    assert t00.top == 32
    assert t00.bottom == 0
    assert t00.left == (0, 16)
    assert t00.right == (36, 16)
    assert t00.center == (18, 16)
    assert t00.topleft == (9, 32)
    assert t00.topright == (27, 32)
    assert t00.bottomleft == (9, 0)
    assert t00.bottomright == (27, 0)
    assert t00.midtop == (18, 32)
    assert t00.midbottom == (18, 0)
    assert t00.midtopleft == (4, 24)
    assert t00.midtopright == (31, 24)
    assert t00.midbottomleft == (4, 8)
    assert t00.midbottomright == (31, 8)

    t01 = m.get((0, 1))
    assert t01.top == 48
    assert t01.bottom == 16
    assert t01.left == t00.topright
    assert t01.right == (63, 32)
    assert t01.center == (45, 32)
    assert t01.topleft == (36, 48)
    assert t01.topright == (54, 48)
    assert t01.bottomleft == t00.right
    assert t01.bottomright == (54, 16)
    assert t01.midtop == (45, 48)
    assert t01.midbottom == (45, 16)
    assert t01.midtopleft == (31, 40)
    assert t01.midtopright == (58, 40)
    assert t01.midbottomleft == t00.midtopright
    assert t01.midbottomright == (58, 24)

    t = m.get((1, 0))
    assert t.top == 32
    assert t.bottom == 0
    assert t.left == t01.bottomright
    assert t.right == (90, 16)
    assert t.center == (72, 16)
    assert t.topleft == t01.right
    assert t.midtopleft == t01.midbottomright
