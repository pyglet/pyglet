from pyglet import image

import spryte

class Map(spryte.SpriteBatch):
    '''Rectangular map.

    "cells" argument must be a row-major list of lists of Sprite instances.
    '''
    def set_cells(self, cell_width, cell_height, cells, origin=None):
        self.cell_width, self.cell_height = cell_width, cell_height
        if origin is None:
            origin = (0, 0)
        self.x, self.y = origin
        self.cells = cells
        self.pixel_width = len(cells[0]) * cell_width
        self.pixel_height = len(cells) * cell_height

    def get_cell(self, x, y):
        ''' Return Cell at cell pos=(x,y).

        Return None if out of bounds.'''
        if x < 0 or y < 0:
            return None
        try:
            return self.cells[y][x]
        except IndexError:
            return None

    def get_in_region(self, x1, y1, x2, y2):
        '''Return cells that are within the pixel bounds specified by the
        bottom-left (x1, y1) and top-right (x2, y2) corners.
        '''
        x1 = max(0, x1 // self.cell_width)
        y1 = max(0, y1 // self.cell_height)
        x2 = min(len(self.cells[0]), x2 // self.cell_width + 1)
        y2 = min(len(self.cells), y2 // self.cell_height + 1)
        return [self.cells[y][x] for x in range(x1, x2) for y in range(y1, y2)]
 
    def get(self, x, y):
        ''' Return Cell at pixel px=(x,y).

        Return None if out of bounds.'''
        return self.get_cell(x // self.cell_width, y // self.cell_height)
 
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
        return self.get_cell(cell.x//self.cell_width + dx,
                cell.y//self.cell_height + dy)

    def delete(self):
        for row in self.cells:
            for cell in row:
                cell.delete()
        self.cells = []

    @classmethod
    def from_imagegrid(cls, im, cells, file=None, origin=None):
        '''Initialise the map using an image the image grid.

        Both the image grid and the map cells have y=0 at the bottom of
        the grid / map.

        Return a Map instance.'''
        texture_sequence = im.texture_sequence
        l = []
        cw, ch = texture_sequence.item_width, texture_sequence.item_height
        inst = cls()
        for y, row in enumerate(cells):
            m = []
            l.append(m)
            for x, num in enumerate(row):
                m.append(spryte.Sprite(texture_sequence[num], x*cw, y*ch,
                    map=inst, batch=inst))
        inst.set_cells(cw, ch, l, origin)
        return inst

