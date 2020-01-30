import unittest

from pyglet.image import atlas

__noninteractive = True


class Rect:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def __repr__(self):
        return 'Rect(%d, %d to %d, %d)' % (
            self.x1, self.y1, self.x2, self.y2)

    def intersects(self, other):
        return self.x2 > other.x1 and self.x1 < other.x2 and \
               self.y2 > other.y1 and self.y1 < other.y2


class AllocatorEnvironment:
    def __init__(self, test_case, width, height):
        self.test_case = test_case
        self.rectes = []
        self.allocator = atlas.Allocator(width, height)

    def check(self, test_case):
        for i, rect in enumerate(self.rectes):
            test_case.assertTrue(0 <= rect.x1 < self.allocator.width)
            test_case.assertTrue(0 <= rect.x2 <= self.allocator.width)
            test_case.assertTrue(0 <= rect.y1 < self.allocator.height)
            test_case.assertTrue(0 <= rect.y2 <= self.allocator.height)
            for other in self.rectes[i + 1:]:
                test_case.assertFalse(rect.intersects(other))

    def add(self, width, height):
        x, y = self.allocator.alloc(width, height)
        self.rectes.append(Rect(x, y, x + width, y + height))
        self.check(self.test_case)

    def add_fail(self, width, height):
        self.test_case.assertRaises(atlas.AllocatorException,
                                    self.allocator.alloc, width, height)


class TestPack(unittest.TestCase):
    def test_over_x(self):
        env = AllocatorEnvironment(self, 3, 3)
        env.add_fail(3, 4)

    def test_over_y(self):
        env = AllocatorEnvironment(self, 3, 3)
        env.add_fail(4, 3)

    def test_1(self):
        env = AllocatorEnvironment(self, 4, 4)
        for i in range(16):
            env.add(1, 1)
        env.add_fail(1, 1)

    def test_2(self):
        env = AllocatorEnvironment(self, 3, 3)
        env.add(2, 2)
        for i in range(4):
            env.add(1, 1)

    def test_3(self):
        env = AllocatorEnvironment(self, 3, 3)
        env.add(3, 3)
        env.add_fail(1, 1)

    def test_4(self):
        env = AllocatorEnvironment(self, 5, 4)
        for i in range(4):
            env.add(2, 2)
        env.add_fail(2, 1)
        env.add(1, 2)
        env.add(1, 2)
        env.add_fail(1, 1)

    def test_5(self):
        env = AllocatorEnvironment(self, 4, 4)
        env.add(3, 2)
        env.add(4, 2)
        env.add(1, 2)
        env.add_fail(1, 1)


if __name__ == '__main__':
    unittest.main()
