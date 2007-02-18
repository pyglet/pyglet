#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.gl import *
from pyglet.image import *
from pyglet.window import *

class TestTexture3D(unittest.TestCase):
    def create_image(self, width, height, color):
        data = ('%c' % color) * (width * height)
        return ImageData(width, height, 'L', data)

    def check_image(self, image, width, height, color):
        self.assertTrue(image.width == width)
        self.assertTrue(image.height == height)
        color = '%c' % (color)
        image = image.image_data
        image.pitch = image.width
        image.format = 'L'
        data = image.data
        self.assertTrue(data == color * len(data))

    def setUp(self):
        self.w = Window(visible=False)

    def test2(self):
        # Test 2 images of 32x32
        images = [self.create_image(32, 32, i+1) for i in range(2)]
        texture = Texture3D.create_from_images(images)
        self.assertTrue(len(texture) == 2)
        for i in range(2):
            self.check_image(texture[i], 32, 32, i+1)

    def test5(self):
        # test 5 images of 31x94  (power2 issues)
        images = [self.create_image(31, 94, i+1) for i in range(5)]
        texture = Texture3D.create_from_images(images)
        self.assertTrue(len(texture) == 5)
        for i in range(5):
            self.check_image(texture[i], 31, 94, i+1)

    def testSet(self):
        # test replacing an image
        images = [self.create_image(32, 32, i+1) for i in range(3)]
        texture = Texture3D.create_from_images(images)
        self.assertTrue(len(texture) == 3)
        for i in range(3):
            self.check_image(texture[i], 32, 32, i+1)
        texture[1] = self.create_image(32, 32, 87)
        self.check_image(texture[0], 32, 32, 1)
        self.check_image(texture[1], 32, 32, 87)
        self.check_image(texture[2], 32, 32, 3)

if __name__ == '__main__':
    unittest.main()
