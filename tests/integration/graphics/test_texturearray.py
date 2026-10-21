import unittest

import pytest

from pyglet.enums import AddressMode, ComponentFormat, TextureFilter, TextureType
from pyglet.image import ImageException

from pyglet.graphics.texture import TextureArray, TextureArrayDepthExceeded
from pyglet.image import ImageData, ImageGrid
from pyglet.window import Window

from tests.annotations import skip_graphics_api, GraphicsAPIGroups


def colorbyte(color):
    return bytes((color,))


@skip_graphics_api(GraphicsAPIGroups.GL2)
class TestTextureArray(unittest.TestCase):
    """Test the Texture3D for image grids."""

    def create_image(self, width, height, color):
        data = colorbyte(color) * (width * height)
        return ImageData(width, height, 'R', data)

    def check_image(self, image, width, height, color):
        self.assertTrue(image.width == width)
        self.assertTrue(image.height == height)
        image = image.get_image_data()
        data = image.get_bytes('R', image.width)
        self.assertTrue(data == colorbyte(color) * len(data))

    def set_grid_image(self, itemwidth, itemheight, rows, cols, rowpad, colpad):
        data = b''
        color = 1
        width = itemwidth * cols + colpad * (cols - 1)
        height = itemheight * rows + rowpad * (rows - 1)
        for row in range(rows):
            rowdata = b''
            for col in range(cols):
                rowdata += colorbyte(color) * itemwidth
                if col < cols - 1:
                    rowdata += b'\0' * colpad
                color += 1

            data += rowdata * itemheight
            if row < rows - 1:
                data += (width * b'\0') * rowpad
        assert len(data) == width * height
        self.image = ImageData(width, height, 'R', data)
        self.grid = ImageGrid(self.image, rows, cols,
                         itemwidth, itemheight, rowpad, colpad)
        self.texture_array = TextureArray.create_for_image_grid(self.grid)

    def check_cell(self, cell_texture: TextureArray, cellindex):
        self.assertTrue(cell_texture.width == self.grid.item_width)
        self.assertTrue(cell_texture.height == self.grid.item_height)

        cellimage = cell_texture.get_image_data()
        data = cellimage.get_bytes('R', cellimage.width)
        self.assertTrue(data == colorbyte(cellindex + 1) * len(data))

    def setUp(self):
        self.w = Window(visible=False)

    def tearDown(self) -> None:
        self.w.close()

    def test2(self):
        # Test 2 images of 32x32
        images = [self.create_image(32, 32, i + 1) for i in range(2)]
        texture = TextureArray.create_for_images(images)
        self.assertTrue(len(texture) == 2)
        for i in range(2):
            self.check_image(texture[i], 32, 32, i + 1)

    def test5(self):
        # test 5 images of 31x94  (power2 issues)
        images = [self.create_image(31, 94, i + 1) for i in range(5)]
        texture = TextureArray.create_for_images(images)
        self.assertTrue(len(texture) == 5)
        for i in range(5):
            self.check_image(texture[i], 31, 94, i + 1)

    def testSet(self):
        # test replacing an image
        images = [self.create_image(32, 32, i + 1) for i in range(3)]
        texture = TextureArray.create_for_images(images)
        self.assertTrue(len(texture) == 3)
        for i in range(3):
            self.check_image(texture[i], 32, 32, i + 1)
        texture[1] = self.create_image(32, 32, 87)
        self.check_image(texture[0], 32, 32, 1)
        self.check_image(texture[1], 32, 32, 87)
        self.check_image(texture[2], 32, 32, 3)

        # Test slicing.
        texture[0:2] = [self.create_image(32, 32, 11), self.create_image(32, 32, 22)]
        self.check_image(texture[0], 32, 32, 11)
        self.check_image(texture[1], 32, 32, 22)
        self.check_image(texture[2], 32, 32, 3)

    def testUploadZ(self):
        images = [self.create_image(8, 8, 1) for _ in range(2)]
        texture = TextureArray.create_for_images(images)
        texture.upload(self.create_image(8, 8, 5), 0, 0, 0)
        texture.upload(self.create_image(8, 8, 9), 0, 0, 1)
        self.check_image(texture[0], 8, 8, 5)
        self.check_image(texture[1], 8, 8, 9)

    def testSquare(self):
        # Test a 3x3 grid with no padding and 4x4 images
        rows = cols = 3
        self.set_grid_image(4, 4, rows, cols, 0, 0)
        for i in range(rows * cols):
            self.check_cell(self.grid[i], i)

    def testRect(self):
        # Test a 2x5 grid with no padding and 3x8 images
        rows, cols = 2, 5
        self.set_grid_image(3, 8, rows, cols, 0, 0)
        for i in range(rows * cols):
            self.check_cell(self.grid[i], i)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_texture_array_create_positional_options(test_window):
    test_window.switch_to()
    ctx = test_window.context
    filters = (TextureFilter.NEAREST, TextureFilter.LINEAR)
    texture = TextureArray.create(
        4, 2, TextureType.TYPE_2D_ARRAY, ComponentFormat.RGBA, 8, 'B', filters,
        AddressMode.CLAMP_TO_EDGE, 0, True, False, 1, ctx, max_depth=3,
    )
    try:
        assert texture.max_depth == 3
        assert texture.filters == filters
        assert texture.address_mode == AddressMode.CLAMP_TO_EDGE
        assert texture._context is ctx
        assert texture.valid_mipmaps == (0,)
        assert bytes(texture.fetch(z=2).get_bytes('RGBA', 16)) == bytes(32)
    finally:
        texture.delete()


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_texture_array_create_for_images_options_and_capacity(test_window):
    test_window.switch_to()
    images = [ImageData(2, 2, 'RGBA', bytes((value, 0, 0, 255)) * 4) for value in (21, 43)]
    filters = (TextureFilter.NEAREST, TextureFilter.LINEAR)
    texture = TextureArray.create_for_images(
        images, 8, 'B', filters, AddressMode.CLAMP_TO_EDGE, 0, test_window.context, max_depth=4,
    )
    try:
        assert len(texture) == 2
        assert texture.max_depth == 4
        assert texture.filters == filters
        assert texture.address_mode == AddressMode.CLAMP_TO_EDGE
        assert bytes(texture.fetch(z=1).get_bytes('RGBA', 8)) == bytes((43, 0, 0, 255)) * 4
    finally:
        texture.delete()


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_texture_array_rejects_incompatible_type_and_capacity(test_window):
    cls = TextureArray
    with pytest.raises(ImageException, match='TYPE_2D_ARRAY'):
        cls.create(2, 2, TextureType.TYPE_2D, context=test_window.context)
    with pytest.raises(ImageException, match='Array depth'):
        cls.create(2, 2, max_depth=0, context=test_window.context)
    images = [ImageData(1, 1, 'RGBA', bytes(4)) for _ in range(2)]
    with pytest.raises(TextureArrayDepthExceeded):
        cls.create_for_images(images, max_depth=1, context=test_window.context)


@skip_graphics_api(GraphicsAPIGroups.GL2)
@pytest.mark.parametrize('use_region', [False, True])
def test_texturearray_create_from_image_forwards_positional_options(test_window, use_region):
    test_window.switch_to()
    if use_region:
        source = ImageData(4, 4, 'RGBA', bytes(range(64))).get_region(1, 1, 2, 3)
        expected = b''.join((bytes(range(start, start + 8)) for start in (20, 36, 52)))
    else:
        expected = bytes((17, 53, 89, 255)) * 6
        source = ImageData(2, 3, 'RGBA', expected)
    filters = (TextureFilter.NEAREST, TextureFilter.LINEAR)
    cls = TextureArray
    texture = cls.create_from_image(
        source, TextureType.TYPE_2D_ARRAY, 8, filters, AddressMode.CLAMP_TO_EDGE, 0, test_window.context,
    )
    try:
        assert isinstance(texture, cls)
        assert texture.tex_type == TextureType.TYPE_2D_ARRAY
        assert texture.filters == filters
        assert texture.address_mode == AddressMode.CLAMP_TO_EDGE
        assert texture._context is test_window.context
        assert (texture.width, texture.height) == (2, 3)
        assert bytes(texture.fetch().get_bytes('RGBA', 8)) == expected
        assert len(texture) == 1
    finally:
        texture.delete()


def test_texturearray_create_for_images_rejects_empty_images():
    with pytest.raises(ImageException, match='At least one image'):
        TextureArray.create_for_images([])
