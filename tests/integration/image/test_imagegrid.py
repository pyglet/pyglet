import unittest

from pyglet.image import ImageData, ImageGrid


def colorbyte(color):
    return bytes((color,))


class ImageGridTestCase(unittest.TestCase):
    """Test ImageGrid indexing and slicing over image regions."""

    def set_grid_image(self, item_width: int, item_height: int, rows: int, cols: int, rowpad: int, colpad: int):
        data = b''
        color = 1
        width = item_width * cols + colpad * (cols - 1)
        height = item_height * rows + rowpad * (rows - 1)
        for row in range(rows):
            rowdata = b''
            for col in range(cols):
                rowdata += colorbyte(color) * item_width
                if col < cols - 1:
                    rowdata += b'\0' * colpad
                color += 1

            data += rowdata * item_height
            if row < rows - 1:
                data += (width * b'\0') * rowpad
        assert len(data) == width * height
        self.image = ImageData(width, height, 'R', data)
        self.grid = ImageGrid(
            self.image,
            rows,
            cols,
            item_width,
            item_height,
            rowpad,
            colpad,
        )

    def check_cell(self, cell_image, cellindex):
        self.assertTrue(cell_image.width == self.grid.item_width)
        self.assertTrue(cell_image.height == self.grid.item_height)

        color = colorbyte(cellindex + 1)
        data = cell_image.get_bytes('R', cell_image.width)
        self.assertTrue(data == color * len(data))

    def test_square(self):
        rows = cols = 3
        self.set_grid_image(4, 4, rows, cols, 0, 0)
        for i in range(rows * cols):
            self.check_cell(self.grid[i], i)

    def test_rect(self):
        rows, cols = 2, 5
        self.set_grid_image(3, 8, rows, cols, 0, 0)
        for i in range(rows * cols):
            self.check_cell(self.grid[i], i)

    def test_pad(self):
        rows, cols = 5, 3
        self.set_grid_image(10, 9, rows, cols, 3, 7)
        for i in range(rows * cols):
            self.check_cell(self.grid[i], i)

    def test_tuple(self):
        rows, cols = 3, 4
        self.set_grid_image(5, 5, rows, cols, 0, 0)
        for row in range(rows):
            for col in range(cols):
                self.check_cell(self.grid[(row, col)], row * cols + col)

    def test_range(self):
        rows, cols = 4, 3
        self.set_grid_image(10, 1, rows, cols, 0, 0)
        images = self.grid[4:8]
        for i, image in enumerate(images):
            self.check_cell(image, i + 4)

    def test_tuple_range(self):
        rows, cols = 10, 10
        self.set_grid_image(4, 4, rows, cols, 0, 0)
        images = self.grid[(3, 2):(6, 5)]
        i = 0
        for row in range(3, 6):
            for col in range(2, 5):
                self.check_cell(images[i], row * cols + col)
                i += 1


import pytest

from pyglet.graphics import TextureGrid
from pyglet.image import ImageException


def image(value, width=1):
    return ImageData(width, 1, 'RGBA', bytes((value, value, value, 255)) * width)


@pytest.fixture(params=['image', 'texture'])
def grid(request, test_window):
    pixels = b''.join(bytes((value, value, value, 255)) for value in (10, 20, 30, 40))
    data = ImageData(2, 2, 'RGBA', pixels)
    if request.param == 'image':
        yield ImageGrid(data, 2, 2)
    else:
        texture = data.get_texture()
        yield TextureGrid(texture, 2, 2)
        texture.delete()


def values(grid):
    return [bytes(cell.get_image_data().get_bytes('RGBA', 4))[0] for cell in grid]


@pytest.mark.parametrize('selection', [slice(0, 2), slice(None, None, 2), slice((0, 0), (2, 1))])
@pytest.mark.parametrize('count', [0, 1, 3])
def test_slice_requires_one_image_per_selected_cell(grid, selection, count):
    before = values(grid)
    with pytest.raises(ValueError):
        grid[selection] = [image(100 + i) for i in range(count)]
    assert values(grid) == before


def test_all_dimensions_are_checked_before_any_cell_is_written(grid):
    before = values(grid)
    with pytest.raises(ImageException):
        grid[:2] = [image(100), image(110, width=2)]
    assert values(grid) == before


@pytest.mark.parametrize('selection,expected', [
    (slice(0, 2), [100, 110, 30, 40]),
    (slice(None, None, 2), [100, 20, 110, 40]),
    (slice((0, 0), (2, 1)), [100, 20, 110, 40]),
])
def test_valid_replacements_update_the_requested_cells(grid, selection, expected):
    grid[selection] = [image(100), image(110)]
    assert values(grid) == expected
    assert len(grid) == 4


def test_empty_selection_accepts_only_empty_replacements(grid):
    grid[0:0] = []
    assert values(grid) == [10, 20, 30, 40]
    with pytest.raises(ValueError):
        grid[0:0] = [image(100)]
    assert values(grid) == [10, 20, 30, 40]
