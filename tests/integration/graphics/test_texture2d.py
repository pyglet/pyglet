import unittest

from pyglet.graphics import Texture
from pyglet.image import ImageData
from pyglet.window import Window


def colorbyte(color):
    return bytes((color,))


class TestTextureUploadFetch(unittest.TestCase):
    def setUp(self):
        self.w = Window(visible=False)

    def tearDown(self) -> None:
        self.w.close()

    def create_image(self, width, height, color):
        data = colorbyte(color) * (width * height)
        return ImageData(width, height, 'R', data)

    def test_upload_fetch_2d(self):
        width, height = 4, 4
        data = colorbyte(25) + colorbyte(50) + colorbyte(75) + colorbyte(100)
        data = data * (width * height)
        image = ImageData(width, height, 'RGBA', data)

        texture = Texture.create(width, height, blank_data=True)
        texture.upload(image, 0, 0, 0)

        fetched = texture.get_image_data()
        fetched_bytes = bytes(fetched.get_bytes('RGBA', fetched.width * 4))
        self.assertEqual(fetched_bytes, data)

    def test_region_upload_fetch(self):
        width, height = 4, 4
        base = ImageData(width, height, 'R', colorbyte(0) * (width * height))
        texture = Texture.create(width, height, blank_data=True)
        texture.upload(base, 0, 0, 0)

        region = ImageData(2, 2, 'R', colorbyte(7) * 4)
        texture.upload(region, 1, 1, 0)

        fetched = texture.get_image_data()
        data = fetched.get_bytes('R', fetched.width)
        self.assertEqual(data[5], 7)
        self.assertEqual(data[6], 7)
        self.assertEqual(data[9], 7)
        self.assertEqual(data[10], 7)

    def test_upload_respects_texture_anchor(self):
        width, height = 4, 4
        base = ImageData(width, height, 'R', colorbyte(0) * (width * height))
        texture = Texture.create(width, height, blank_data=True)
        texture.upload(base, 0, 0, 0)

        texture.anchor_x = 1
        texture.anchor_y = 1
        image = ImageData(2, 2, 'R', colorbyte(9) * 4)
        texture.upload(image, 1, 1, 0)

        fetched = texture.get_image_data()
        data = fetched.get_bytes('R', fetched.width)
        self.assertEqual(data[0], 9)
        self.assertEqual(data[1], 9)
        self.assertEqual(data[4], 9)
        self.assertEqual(data[5], 9)

    def test_upload_invalid_level(self):
        texture = Texture.create(4, 4, blank_data=True)
        with self.assertRaisesRegex(Exception, "Mipmap level must be non-negative"):
            texture.upload(self.create_image(2, 2, 1), 0, 0, 0, level=-1)
