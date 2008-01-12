
class Rect(object):
    '''Define a rectangular area.

    Many convenience handles and other properties are also defined - all of
    which may be assigned to which will result in altering the position
    and sometimes dimensions of the Rect.

    The Rect area includes the bottom and left borders but not the top and
    right borders.
    '''
    def __init__(self, x, y, width, height):
        '''Create a Rect with the bottom-left corner at (x, y) and
        dimensions (width, height).
        '''
        self._x, self._y = x, y
        self._width, self._height = width, height

    # the following four properties will most likely be overridden in a
    # subclass
    def set_x(self, value): self._x = value
    x = property(lambda self: self._x, set_x)
    def set_y(self, value): self._y = value
    y = property(lambda self: self._y, set_y)
    def set_width(self, value): self._width = value
    width = property(lambda self: self._width, set_width)
    def set_height(self, value): self._height = value
    height = property(lambda self: self._height, set_height)
    def set_pos(self, value): self._x, self._y = value
    pos = property(lambda self: (self._x, self._y), set_pos)
    def set_size(self, value): self._width, self._height = value
    size = property(lambda self: (self._width, self._height), set_size)

    def contains(self, x, y):
        '''Return boolean whether the point defined by x, y is inside the
        rect area.
        '''
        if x < self._x or x > self._x + self._width: return False
        if y < self._y or y > self._y + self._height: return False
        return True

    def intersects(self, other):
        '''Return boolean whether the "other" rect (an object with .x, .y,
        .width and .height attributes) overlaps this Rect in any way.
        '''
        if self._x + self._width < other.x: return False
        if other.x + other.width < self._x: return False
        if self._y + self._height < other.y: return False
        if other.y + other.height < self._y: return False
        return True

    # r/w, in pixels, y extent
    def get_top(self): return self.y + self.height
    def set_top(self, y): self.y = y - self.height
    top = property(get_top, set_top)

    # r/w, in pixels, y extent
    def get_bottom(self): return self.y
    def set_bottom(self, y): self.y = y
    bottom = property(get_bottom, set_bottom)

    # r/w, in pixels, x extent
    def get_left(self): return self.x
    def set_left(self, x): self.x = x
    left = property(get_left, set_left)

    # r/w, in pixels, x extent
    def get_right(self): return self.x + self.width
    def set_right(self, x): self.x = x - self.width
    right = property(get_right, set_right)

    # r/w, in pixels, (x, y)
    def get_center(self):
        return (self.x + self.width/2, self.y + self.height/2)
    def set_center(self, center):
        x, y = center
        self.pos = (x - self.width/2, y - self.height/2)
    center = property(get_center, set_center)

    # r/w, in pixels, (x, y)
    def get_midtop(self):
        return (self.x + self.width/2, self.y + self.height)
    def set_midtop(self, midtop):
        x, y = midtop
        self.pos = (x - self.width/2, y - self.height)
    midtop = property(get_midtop, set_midtop)

    # r/w, in pixels, (x, y)
    def get_midbottom(self):
        return (self.x + self.width/2, self.y)
    def set_midbottom(self, midbottom):
        x, y = midbottom
        self.pos = (x - self.width/2, y)
    midbottom = property(get_midbottom, set_midbottom)

    # r/w, in pixels, (x, y)
    def get_midleft(self):
        return (self.x, self.y + self.height/2)
    def set_midleft(self, midleft):
        x, y = midleft
        self.pos = (x, y - self.height/2)
    midleft = property(get_midleft, set_midleft)

    # r/w, in pixels, (x, y)
    def get_midright(self):
        return (self.x + self.width, self.y + self.height/2)
    def set_midright(self, midright):
        x, y = midright
        self.pos = (x - self.width, y - self.height/2)
    midright = property(get_midright, set_midright)
 
    # r/w, in pixels, (x, y)
    def get_topleft(self):
        return (self.x, self.y + self.height)
    def set_topleft(self, pos):
        x, y = pos
        self.pos = (x, y - self.height)
    topleft = property(get_topleft, set_topleft)
 
    # r/w, in pixels, (x, y)
    def get_topright(self):
        return (self.x + self.width, self.y + self.height)
    def set_topright(self, pos):
        x, y = pos
        self.pos = (x - self.width, y - self.height)
    topright = property(get_topright, set_topright)
 
    # r/w, in pixels, (x, y)
    def get_bottomright(self):
        return (self.x + self.width, self.y)
    def set_bottomright(self, pos):
        x, y = pos
        self.pos = (x - self.width, y)
    bottomright = property(get_bottomright, set_bottomright)
 
    # r/w, in pixels, (x, y)
    def get_bottomleft(self):
        return (self.x, self.y)
    def set_bottomleft(self, pos):
        self.x, self.y = pos
    bottomleft = property(get_bottomleft, set_bottomleft)

