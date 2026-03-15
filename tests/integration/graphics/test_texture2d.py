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
        pixel = colorbyte(color) * 3 + colorbyte(255)
        data = pixel * (width * height)
        return ImageData(width, height, 'RGBA', data)

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
        base = self.create_image(width, height, 0)
        texture = Texture.create(width, height, blank_data=True)
        texture.upload(base, 0, 0, 0)

        region = self.create_image(2, 2, 7)
        texture.upload(region, 1, 1, 0)

        fetched = texture.get_image_data()
        data = fetched.get_bytes('RGBA', fetched.width * 4)
        self.assertEqual(data[5 * 4], 7)
        self.assertEqual(data[6 * 4], 7)
        self.assertEqual(data[9 * 4], 7)
        self.assertEqual(data[10 * 4], 7)

    def test_upload_respects_texture_anchor(self):
        width, height = 4, 4
        base = self.create_image(width, height, 0)
        texture = Texture.create(width, height, blank_data=True)
        texture.upload(base, 0, 0, 0)

        texture.anchor_x = 1
        texture.anchor_y = 1
        image = self.create_image(2, 2, 9)
        texture.upload(image, 1, 1, 0)

        fetched = texture.get_image_data()
        data = fetched.get_bytes('RGBA', fetched.width * 4)
        self.assertEqual(data[0 * 4], 9)
        self.assertEqual(data[1 * 4], 9)
        self.assertEqual(data[4 * 4], 9)
        self.assertEqual(data[5 * 4], 9)

    def test_upload_invalid_level(self):
        texture = Texture.create(4, 4, blank_data=True)
        with self.assertRaisesRegex(Exception, "Mipmap level must be non-negative"):
            texture.upload(self.create_image(2, 2, 1), 0, 0, 0, level=-1)
