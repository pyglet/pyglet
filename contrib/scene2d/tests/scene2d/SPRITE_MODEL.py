#!/usr/bin/env python

'''Testing the sprite model.

This test should just run without failing.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.window import Window
from pyglet.image import SolidColorImagePattern
from scene2d import Sprite, Image2d

class SpriteModelTest(unittest.TestCase):

    def setUp(self):
        self.w = Window(width=1, height=1, visible=False)
        self.s = Sprite(10, 10, 10, 10,
            Image2d.from_image(SolidColorImagePattern((0, 0, 0,
                0)).create_image(1, 1)))
        assert (self.s.x, self.s.y) == (10, 10)

    def tearDown(self):
        self.w.close()

    def test_top(self):
        assert self.s.top == 20
        self.s.top = 10
        assert (self.s.x, self.s.y) == (10, 0)

    def test_bottom(self):
        assert self.s.bottom == 10
        self.s.bottom = 0
        assert (self.s.x, self.s.y) == (10, 0)

    def test_right(self):
        assert self.s.right == 20
        self.s.right = 10
        assert (self.s.x, self.s.y) == (0, 10)

    def test_left(self):
        assert self.s.left == 10
        self.s.left = 0
        assert (self.s.x, self.s.y) == (0, 10)

    def test_center(self):
        assert self.s.center == (15, 15)
        self.s.center = (5, 5)
        assert (self.s.x, self.s.y) == (0, 0)

    def test_midtop(self):
        assert self.s.midtop == (15, 20)
        self.s.midtop = (5, 5)
        assert (self.s.x, self.s.y) == (0, -5)

    def test_midbottom(self):
        assert self.s.midbottom == (15, 10)
        self.s.midbottom = (5, 5)
        assert (self.s.x, self.s.y) == (0, 5)

    def test_midleft(self):
        assert self.s.midleft == (10, 15)
        self.s.midleft = (5, 5)
        assert (self.s.x, self.s.y) == (5, 0)

    def test_midright(self):
        assert self.s.midright == (20, 15)
        self.s.midright = (5, 5)
        assert (self.s.x, self.s.y) == (-5, 0)

    def test_topleft(self):
        assert self.s.topleft == (10, 20)
        self.s.topleft = (5, 5)
        assert (self.s.x, self.s.y) == (5, -5)

    def test_topright(self):
        assert self.s.topright == (20, 20)
        self.s.topright = (5, 5)
        assert (self.s.x, self.s.y) == (-5, -5)

    def test_bottomright(self):
        assert self.s.bottomright == (20, 10)
        self.s.bottomright = (5, 5)
        assert (self.s.x, self.s.y) == (-5, 5)

    def test_bottomleft(self):
        assert self.s.bottomleft == (10, 10)
        self.s.bottomleft = (5, 5)
        assert (self.s.x, self.s.y) == (5, 5)

if __name__ == '__main__':
    unittest.main()
