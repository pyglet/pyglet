import unittest

import pyglet

from pyglet.enums import ComponentFormat
from pyglet.graphics import Texture, PixelData, TextureAtlas
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

    def test_upload_invalid_level(self):
        texture = Texture.create(4, 4, blank_data=True)
        with self.assertRaisesRegex(Exception, "Mipmap level must be non-negative"):
            texture.upload(self.create_image(2, 2, 1), 0, 0, 0, level=-1)



def test_pixel_data_pitch_bytes_and_image_view():
    data = bytearray(3 * 2 * 4 * 4)
    pixels = PixelData(3, 2, ComponentFormat.RGBA, "f", data)

    assert pixels.pitch == 3 * 4 * 4
    assert bytes(pixels) == bytes(data)

    image_data = pixels.to_image_data()
    assert image_data._current_data is data  # noqa: SLF001
    assert image_data.data_type == "f"
    assert image_data.pitch == pixels.pitch


def test_texture_fetch_can_be_saved(test_window, tmp_path):
    width, height = 4, 3
    data = bytes(
        component
        for y in range(height)
        for x in range(width)
        for component in (x, y, x + y, 255)
    )
    texture = Texture.create(width, height, blank_data=True, context=test_window.context)
    texture.upload(ImageData(width, height, 'RGBA', data), 0, 0, 0)

    filename = tmp_path / 'texture.png'
    texture.fetch().save(str(filename))

    loaded = pyglet.image.load(str(filename))
    assert (loaded.width, loaded.height) == (width, height)
    assert loaded.get_bytes('RGBA', width * 4) == data


def test_texture_region_fetch_can_be_saved(test_window, tmp_path):
    width, height = 4, 3
    data = bytes(
        component
        for y in range(height)
        for x in range(width)
        for component in (x, y, x + y, 255)
    )
    texture = Texture.create(width, height, blank_data=True, context=test_window.context)
    texture.upload(ImageData(width, height, 'RGBA', data), 0, 0, 0)

    filename = tmp_path / 'region.png'
    texture.get_region(1, 1, 2, 2).fetch().save(str(filename))

    loaded = pyglet.image.load(str(filename))
    expected = b''.join(
        data[(y * width + 1) * 4:(y * width + 3) * 4]
        for y in range(1, 3)
    )
    assert (loaded.width, loaded.height) == (2, 2)
    assert loaded.get_bytes('RGBA', 2 * 4) == expected


def test_texture_regions_have_their_root_texture_as_owner(test_window):
    texture = Texture.create(4, 4, blank_data=True, context=test_window.context)
    region = texture.get_region(1, 1, 2, 2)
    nested_region = region.get_region(0, 0, 1, 1)

    atlas = TextureAtlas(width=4, height=4)
    atlas_region = atlas.add(ImageData(1, 1, 'RGBA', bytes((1, 2, 3, 255))))

    assert texture.owner is texture
    assert region.owner is texture
    assert nested_region.owner is texture
    assert atlas.texture.owner is atlas.texture
    assert atlas_region.owner is atlas.texture
