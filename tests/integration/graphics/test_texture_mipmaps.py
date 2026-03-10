import unittest

from pyglet.graphics import Texture, Texture3D
from pyglet.graphics.texture import TextureArray
from pyglet.image import ImageData
from pyglet.window import Window

from tests.annotations import skip_graphics_api, GraphicsAPI


def colorbyte(color):
    return bytes((color,))


class TestTextureMipmaps2D(unittest.TestCase):
    def setUp(self):
        self.w = Window(visible=False)

    def tearDown(self) -> None:
        self.w.close()

    def create_image(self, width, height, color):
        pixel = colorbyte(color) * 3 + colorbyte(255)
        data = pixel * (width * height)
        return ImageData(width, height, 'RGBA', data)

    def test_texture2d_init_and_upload_levels(self):
        texture = Texture.create(8, 4, blank_data=False)
        self.assertEqual(texture.mipmap_count, 1)
        self.assertEqual(texture.valid_mipmaps, ())

        texture.init_mipmaps(levels=3, blank_data=False)
        self.assertEqual(texture.mipmap_count, 3)
        self.assertEqual(texture.valid_mipmaps, ())

        with self.assertRaisesRegex(Exception, "Mipmap level must be non-negative"):
            texture.upload(self.create_image(8, 4, 1), 0, 0, 0, level=-1)

        texture.upload(self.create_image(8, 4, 1), 0, 0, 0, level=0)
        self.assertIn(0, texture.valid_mipmaps)

        with self.assertRaisesRegex(Exception, "not initialized"):
            texture.upload(self.create_image(2, 1, 3), 0, 0, 0, level=4)

        texture.upload(self.create_image(2, 1, 2), 0, 0, 0, level=2)
        self.assertEqual(texture.valid_mipmaps, (0, 2))

    def test_texture2d_generate_mipmaps(self):
        texture = Texture.create(8, 4, blank_data=True)
        texture.generate_mipmaps()
        self.assertEqual(texture.mipmap_count, 4)
        self.assertEqual(texture.valid_mipmaps, (0, 1, 2, 3))

    def test_texture2d_init_errors(self):
        texture = Texture.create(4, 4, blank_data=False)
        with self.assertRaisesRegex(Exception, "at least 1"):
            texture.init_mipmaps(levels=0)
        with self.assertRaisesRegex(Exception, "cannot exceed"):
            texture.init_mipmaps(levels=10)


@skip_graphics_api(GraphicsAPI.GL2)
class TestTextureMipmapsArrays(unittest.TestCase):
    def setUp(self):
        self.w = Window(visible=False)

    def tearDown(self) -> None:
        self.w.close()

    def create_image(self, width, height, color):
        pixel = colorbyte(color) * 3 + colorbyte(255)
        data = pixel * (width * height)
        return ImageData(width, height, 'RGBA', data)

    def test_texture3d_mipmap_depth(self):
        images = [self.create_image(8, 4, i + 1) for i in range(4)]
        texture = Texture3D.create_for_images(images)
        self.assertEqual(texture._get_mipmap_depth(0), 4)
        self.assertEqual(texture._get_mipmap_depth(1), 2)
        self.assertEqual(texture._get_mipmap_depth(2), 1)
        texture.init_mipmaps()
        self.assertEqual(texture.mipmap_count, 4)

        texture.upload(self.create_image(8, 4, 7), 0, 0, 0, level=0)
        texture.upload(self.create_image(4, 2, 8), 0, 0, 0, level=1)
        self.assertIn(0, texture.valid_mipmaps)
        self.assertIn(1, texture.valid_mipmaps)

    def test_texture_array_mipmap_depth(self):
        images = [self.create_image(8, 4, i + 1) for i in range(4)]
        texture = TextureArray.create_for_images(images)
        self.assertEqual(texture._get_mipmap_depth(0), 4)
        self.assertEqual(texture._get_mipmap_depth(2), 4)
        texture.init_mipmaps()
        self.assertEqual(texture.mipmap_count, 4)

        texture.upload(self.create_image(8, 4, 7), 0, 0, 0, level=0)
        texture.upload(self.create_image(4, 2, 8), 0, 0, 0, level=1)
        self.assertIn(0, texture.valid_mipmaps)
        self.assertIn(1, texture.valid_mipmaps)
