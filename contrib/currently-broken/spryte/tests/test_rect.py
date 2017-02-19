#!/usr/bin/env python

import unittest

import rect

class RectTest(unittest.TestCase):
    def setUp(self):
        self.r = rect.Rect(10, 10, 10, 10)

    def test_top(self):
        assert self.r.top == 20
        self.r.top = 10
        assert (self.r.x, self.r.y) == (10, 0)

    def test_bottom(self):
        assert self.r.bottom == 10
        self.r.bottom = 0
        assert (self.r.x, self.r.y) == (10, 0)

    def test_right(self):
        assert self.r.right == 20
        self.r.right = 10
        assert (self.r.x, self.r.y) == (0, 10)

    def test_left(self):
        assert self.r.left == 10
        self.r.left = 0
        assert (self.r.x, self.r.y) == (0, 10)

    def test_center(self):
        assert self.r.center == (15, 15)
        self.r.center = (5, 5)
        assert (self.r.x, self.r.y) == (0, 0)

    def test_midtop(self):
        assert self.r.midtop == (15, 20)
        self.r.midtop = (5, 5)
        assert (self.r.x, self.r.y) == (0, -5)

    def test_midbottom(self):
        assert self.r.midbottom == (15, 10)
        self.r.midbottom = (5, 5)
        assert (self.r.x, self.r.y) == (0, 5)

    def test_midleft(self):
        assert self.r.midleft == (10, 15)
        self.r.midleft = (5, 5)
        assert (self.r.x, self.r.y) == (5, 0)

    def test_midright(self):
        assert self.r.midright == (20, 15)
        self.r.midright = (5, 5)
        assert (self.r.x, self.r.y) == (-5, 0)

    def test_topleft(self):
        assert self.r.topleft == (10, 20)
        self.r.topleft = (5, 5)
        assert (self.r.x, self.r.y) == (5, -5)

    def test_topright(self):
        assert self.r.topright == (20, 20)
        self.r.topright = (5, 5)
        assert (self.r.x, self.r.y) == (-5, -5)

    def test_bottomright(self):
        assert self.r.bottomright == (20, 10)
        self.r.bottomright = (5, 5)
        assert (self.r.x, self.r.y) == (-5, 5)

    def test_bottomleft(self):
        assert self.r.bottomleft == (10, 10)
        self.r.bottomleft = (5, 5)
        assert (self.r.x, self.r.y) == (5, 5)

if __name__ == '__main__':
    unittest.main()
