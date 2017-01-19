#!/usr/bin/env python

'''Testing the map model.

This test should just run without failing.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.window import Window
from scene2d import RectMap, HexMap, RectCell, HexCell
from scene2d.debug import gen_hex_map, gen_rect_map

rmd = [
   [ {'meta': x} for x in m ] for m in ['ad', 'be', 'cf']
]
hmd = [
   [ {'meta': x} for x in m ] for m in ['ab', 'cd', 'ef', 'gh']
]

class MapModelTest(unittest.TestCase):
    def setUp(self):
        self.w = Window(width=1, height=1, visible=False)

    def tearDown(self):
        self.w.close()

    def test_rect_neighbor(self):
        # test rectangular tile map
        #    +---+---+---+
        #    | d | e | f |
        #    +---+---+---+
        #    | a | b | c |
        #    +---+---+---+
        m = gen_rect_map(rmd, 10, 16)
        t = m.get_cell(0,0)
        assert (t.x, t.y) == (0, 0) and t.properties['meta'] == 'a'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).properties['meta'] == 'd'
        assert m.get_neighbor(t, m.LEFT) is None
        assert m.get_neighbor(t, m.RIGHT).properties['meta'] == 'b'
        t = m.get_neighbor(t, m.UP)
        assert (t.x, t.y) == (0, 1) and t.properties['meta'] == 'd'
        assert m.get_neighbor(t, m.DOWN).properties['meta'] == 'a'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.LEFT) is None
        assert m.get_neighbor(t, m.RIGHT).properties['meta'] == 'e'
        t = m.get_neighbor(t, m.RIGHT)
        assert (t.x, t.y) == (1, 1) and t.properties['meta'] == 'e'
        assert m.get_neighbor(t, m.DOWN).properties['meta'] == 'b'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.RIGHT).properties['meta'] == 'f'
        assert m.get_neighbor(t, m.LEFT).properties['meta'] == 'd'
        t = m.get_neighbor(t, m.RIGHT)
        assert (t.x, t.y) == (2, 1) and t.properties['meta'] == 'f'
        assert m.get_neighbor(t, m.DOWN).properties['meta'] == 'c'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.RIGHT) is None
        assert m.get_neighbor(t, m.LEFT).properties['meta'] == 'e'
        t = m.get_neighbor(t, m.DOWN)
        assert (t.x, t.y) == (2, 0) and t.properties['meta'] == 'c'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).properties['meta'] == 'f'
        assert m.get_neighbor(t, m.RIGHT) is None
        assert m.get_neighbor(t, m.LEFT).properties['meta'] == 'b'

    def test_rect_coords(self):
        # test rectangular tile map
        #    +---+---+---+
        #    | d | e | f |
        #    +---+---+---+
        #    | a | b | c |
        #    +---+---+---+
        m = gen_rect_map(rmd, 10, 16)

        # test tile sides / corners
        t = m.get_cell(0,0)
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

    def test_rect_pixel(self):
        # test rectangular tile map
        #    +---+---+---+
        #    | d | e | f |
        #    +---+---+---+
        #    | a | b | c |
        #    +---+---+---+
        m = gen_rect_map(rmd, 10, 16)
        t = m.get(0,0)
        assert (t.x, t.y) == (0, 0) and t.properties['meta'] == 'a'
        t = m.get(9,15)
        assert (t.x, t.y) == (0, 0) and t.properties['meta'] == 'a'
        t = m.get(10,15)
        assert (t.x, t.y) == (1, 0) and t.properties['meta'] == 'b'
        t = m.get(9,16)
        assert (t.x, t.y) == (0, 1) and t.properties['meta'] == 'd'
        t = m.get(10,16)
        assert (t.x, t.y) == (1, 1) and t.properties['meta'] == 'e'

    def test_hex_neighbor(self):
        # test hexagonal tile map
        # tiles = [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'h']]
        #   /d\ /h\
        # /b\_/f\_/
        # \_/c\_/g\
        # /a\_/e\_/
        # \_/ \_/ 
        m = gen_hex_map(hmd, 32)
        t = m.get_cell(0,0)
        assert (t.x, t.y) == (0, 0) and t.properties['meta'] == 'a'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).properties['meta'] == 'b'
        assert m.get_neighbor(t, m.DOWN_LEFT) is None
        assert m.get_neighbor(t, m.DOWN_RIGHT) is None
        assert m.get_neighbor(t, m.UP_LEFT) is None
        assert m.get_neighbor(t, m.UP_RIGHT).properties['meta'] == 'c'
        t = m.get_neighbor(t, m.UP)
        assert (t.x, t.y) == (0, 1) and t.properties['meta'] == 'b'
        assert m.get_neighbor(t, m.DOWN).properties['meta'] == 'a'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.DOWN_LEFT) is None
        assert m.get_neighbor(t, m.DOWN_RIGHT).properties['meta'] == 'c'
        assert m.get_neighbor(t, m.UP_LEFT) is None
        assert m.get_neighbor(t, m.UP_RIGHT).properties['meta'] == 'd'
        t = m.get_neighbor(t, m.DOWN_RIGHT)
        assert (t.x, t.y) == (1, 0) and t.properties['meta'] == 'c'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).properties['meta'] == 'd'
        assert m.get_neighbor(t, m.DOWN_LEFT).properties['meta'] == 'a'
        assert m.get_neighbor(t, m.DOWN_RIGHT).properties['meta'] == 'e'
        assert m.get_neighbor(t, m.UP_LEFT).properties['meta'] == 'b'
        assert m.get_neighbor(t, m.UP_RIGHT).properties['meta'] == 'f'
        t = m.get_neighbor(t, m.UP_RIGHT)
        assert (t.x, t.y) == (2, 1) and t.properties['meta'] == 'f'
        assert m.get_neighbor(t, m.DOWN).properties['meta'] == 'e'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.DOWN_LEFT).properties['meta'] == 'c'
        assert m.get_neighbor(t, m.DOWN_RIGHT).properties['meta'] == 'g'
        assert m.get_neighbor(t, m.UP_LEFT).properties['meta'] == 'd'
        assert m.get_neighbor(t, m.UP_RIGHT).properties['meta'] == 'h'
        t = m.get_neighbor(t, m.DOWN_RIGHT)
        assert (t.x, t.y) == (3, 0) and t.properties['meta'] == 'g'
        assert m.get_neighbor(t, m.DOWN) is None
        assert m.get_neighbor(t, m.UP).properties['meta'] == 'h'
        assert m.get_neighbor(t, m.DOWN_LEFT).properties['meta'] == 'e'
        assert m.get_neighbor(t, m.DOWN_RIGHT) is None
        assert m.get_neighbor(t, m.UP_LEFT).properties['meta'] == 'f'
        assert m.get_neighbor(t, m.UP_RIGHT) is None
        t = m.get_neighbor(t, m.UP)
        assert (t.x, t.y) == (3, 1) and t.properties['meta'] == 'h'
        assert m.get_neighbor(t, m.DOWN).properties['meta'] == 'g'
        assert m.get_neighbor(t, m.UP) is None
        assert m.get_neighbor(t, m.DOWN_LEFT).properties['meta'] == 'f'
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
        m = gen_hex_map(hmd, 32)

        # test tile sides / corners
        t00 = m.get_cell(0, 0)
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

        t10 = m.get_cell(1, 0)
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

        t = m.get_cell(2, 0)
        assert t.top == 32
        assert t.bottom == 0
        assert t.left == t10.bottomright
        assert t.right == (90, 16)
        assert t.center == (72, 16)
        assert t.topleft == t10.right
        assert t.midtopleft == t10.midbottomright

    def test_hex_pixel(self):
        # test hexagonal tile map
        # tiles = [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'h']]
        #   /d\ /h\
        # /b\_/f\_/
        # \_/c\_/g\
        # /a\_/e\_/
        # \_/ \_/ 
        m = gen_hex_map(hmd, 32)
        t = m.get(0,0)
        assert t is None
        t = m.get(0,16)
        assert (t.x, t.y) == (0, 0) and t.properties['meta'] == 'a'
        t = m.get(16,16)
        assert (t.x, t.y) == (0, 0) and t.properties['meta'] == 'a'
        t = m.get(35,16)
        assert (t.x, t.y) == (0, 0) and t.properties['meta'] == 'a'
        t = m.get(36,16)
        assert (t.x, t.y) == (1, 0) and t.properties['meta'] == 'c'

    def test_hex_dimensions(self):
        m = gen_hex_map([[{'a':'a'}]], 32)
        assert m.pxw, m.pxh == (36, 32)
        m = gen_hex_map([[{'a':'a'}]*2], 32)
        assert m.pxw, m.pxh == (36, 64)
        m = gen_hex_map([[{'a':'a'}]]*2, 32)
        assert m.pxw, m.pxh == (63, 48)

if __name__ == '__main__':
    unittest.main()
