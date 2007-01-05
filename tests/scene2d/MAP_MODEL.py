#!/usr/bin/env python

'''Testing the map model.

This test should just run without failing.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.scene2d import Map, HexMap, Cell, HexCell

def _cells(l, w, h, klass):
    r = []
    for i, m in enumerate(l):
        c = []
        r.append(c)
        for j, n in enumerate(m):
            c.append(klass(i, j, w, h, n, None))
    return r

class MapModelTest(unittest.TestCase):

    def test_rect_neighbor(self):
        # test rectangular tile map
        #    +---+---+---+
        #    | d | e | f |
        #    +---+---+---+
        #    | a | b | c |
        #    +---+---+---+
        m = Map(10, 16, cells=_cells(['ad', 'be', 'cf'], 10, 16, Cell))
        t = m.get((0,0))
        assert (t.x, t.y) == (0, 0) and t.meta == 'a'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).meta == 'd'
        assert m.get_neighbor(t, m.LEFT) is None
        assert m.get_neighbor(t, m.RIGHT).meta == 'b'
        t = m.get_neighbor(t, m.UP)
        assert (t.x, t.y) == (0, 1) and t.meta == 'd'
        assert m.get_neighbor(t, m.DOWN).meta == 'a'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.LEFT) is None
        assert m.get_neighbor(t, m.RIGHT).meta == 'e'
        t = m.get_neighbor(t, m.RIGHT)
        assert (t.x, t.y) == (1, 1) and t.meta == 'e'
        assert m.get_neighbor(t, m.DOWN).meta == 'b'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.RIGHT).meta == 'f'
        assert m.get_neighbor(t, m.LEFT).meta == 'd'
        t = m.get_neighbor(t, m.RIGHT)
        assert (t.x, t.y) == (2, 1) and t.meta == 'f'
        assert m.get_neighbor(t, m.DOWN).meta == 'c'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.RIGHT) is None
        assert m.get_neighbor(t, m.LEFT).meta == 'e'
        t = m.get_neighbor(t, m.DOWN)
        assert (t.x, t.y) == (2, 0) and t.meta == 'c'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).meta == 'f'
        assert m.get_neighbor(t, m.RIGHT) is None
        assert m.get_neighbor(t, m.LEFT).meta == 'b'

    def test_rect_coords(self):
        # test rectangular tile map
        #    +---+---+---+
        #    | d | e | f |
        #    +---+---+---+
        #    | a | b | c |
        #    +---+---+---+
        m = Map(10, 16, cells=_cells(['ad', 'be', 'cf'], 10, 16, Cell))

        # test tile sides / corners
        t = m.get((0,0))
        assert t.top == 16
        assert t.bottom == 0
        assert t.left == 0
        assert t.right == 10
        assert t.topleft == (0, 16)
        assert t.topright == (10, 16)
        assert t.bottomleft == (0, 0)
        assert t.bottomright == (10, 0)
        assert t.midtop == (5, 16)
        assert t.midleft == (0, 8)
        assert t.midright == (10, 8)
        assert t.midbottom == (5, 0)

    def test_hex_neighbor(self):
        # test hexagonal tile map
        # tiles = [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'h']]
        #   /d\ /h\
        # /b\_/f\_/
        # \_/c\_/g\
        # /a\_/e\_/
        # \_/ \_/ 
        m = HexMap(32, cells=_cells(['ab', 'cd', 'ef', 'gh'], 36, 32, HexCell))
        t = m.get((0,0))
        assert (t.x, t.y) == (0, 0) and t.meta == 'a'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).meta == 'b'
        assert m.get_neighbor(t, m.DOWN_LEFT) is None
        assert m.get_neighbor(t, m.DOWN_RIGHT) is None
        assert m.get_neighbor(t, m.UP_LEFT) is None
        assert m.get_neighbor(t, m.UP_RIGHT).meta == 'c'
        t = m.get_neighbor(t, m.UP)
        assert (t.x, t.y) == (0, 1) and t.meta == 'b'
        assert m.get_neighbor(t, m.DOWN).meta == 'a'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.DOWN_LEFT) is None
        assert m.get_neighbor(t, m.DOWN_RIGHT).meta == 'c'
        assert m.get_neighbor(t, m.UP_LEFT) is None
        assert m.get_neighbor(t, m.UP_RIGHT).meta == 'd'
        t = m.get_neighbor(t, m.DOWN_RIGHT)
        assert (t.x, t.y) == (1, 0) and t.meta == 'c'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).meta == 'd'
        assert m.get_neighbor(t, m.DOWN_LEFT).meta == 'a'
        assert m.get_neighbor(t, m.DOWN_RIGHT).meta == 'e'
        assert m.get_neighbor(t, m.UP_LEFT).meta == 'b'
        assert m.get_neighbor(t, m.UP_RIGHT).meta == 'f'
        t = m.get_neighbor(t, m.UP_RIGHT)
        assert (t.x, t.y) == (2, 1) and t.meta == 'f'
        assert m.get_neighbor(t, m.DOWN).meta == 'e'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.DOWN_LEFT).meta == 'c'
        assert m.get_neighbor(t, m.DOWN_RIGHT).meta == 'g'
        assert m.get_neighbor(t, m.UP_LEFT).meta == 'd'
        assert m.get_neighbor(t, m.UP_RIGHT).meta == 'h'
        t = m.get_neighbor(t, m.DOWN_RIGHT)
        assert (t.x, t.y) == (3, 0) and t.meta == 'g'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).meta == 'h'
        assert m.get_neighbor(t, m.DOWN_LEFT).meta == 'e'
        assert m.get_neighbor(t, m.DOWN_RIGHT) is None
        assert m.get_neighbor(t, m.UP_LEFT).meta == 'f'
        assert m.get_neighbor(t, m.UP_RIGHT) is None
        t = m.get_neighbor(t, m.UP)
        assert (t.x, t.y) == (3, 1) and t.meta == 'h'
        assert m.get_neighbor(t, m.DOWN).meta == 'g'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.DOWN_LEFT).meta == 'f'
        assert m.get_neighbor(t, m.DOWN_RIGHT) is None
        assert m.get_neighbor(t, m.UP_LEFT) is None
        assert m.get_neighbor(t, m.UP_RIGHT) is None

    def test_hex_coords(self):
        # test hexagonal tile map
        # tiles = [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'h']]
        #   /d\ /h\
        # /b\_/f\_/
        # \_/c\_/g\
        # /a\_/e\_/
        # \_/ \_/ 
        m = HexMap(32, cells=_cells(['ad', 'be', 'cf', 'gh'], 36, 32, HexCell))

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

        t10 = m.get((1, 0))
        assert t10.top == 48
        assert t10.bottom == 16
        assert t10.left == t00.topright
        assert t10.right == (63, 32)
        assert t10.center == (45, 32)
        assert t10.topleft == (36, 48)
        assert t10.topright == (54, 48)
        assert t10.bottomleft == t00.right
        assert t10.bottomright == (54, 16)
        assert t10.midtop == (45, 48)
        assert t10.midbottom == (45, 16)
        assert t10.midtopleft == (31, 40)
        assert t10.midtopright == (58, 40)
        assert t10.midbottomleft == t00.midtopright
        assert t10.midbottomright == (58, 24)

        t = m.get((2, 0))
        assert t.top == 32
        assert t.bottom == 0
        assert t.left == t10.bottomright
        assert t.right == (90, 16)
        assert t.center == (72, 16)
        assert t.topleft == t10.right
        assert t.midtopleft == t10.midbottomright


if __name__ == '__main__':
    unittest.main()
