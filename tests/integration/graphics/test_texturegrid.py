import unittest

from pyglet.graphics import TextureAtlas
from pyglet.graphics import TextureGrid
from pyglet.image import ImageData, ImageGrid
from pyglet.window import Window


def colorbyte(color):
    return bytes((color,))


class TextureGridTestCase(unittest.TestCase):
    """Test texture sequence behavior produced by ImageGrid."""

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
        image_grid = ImageGrid(
            self.image,
            rows,
            cols,
            item_width,
            item_height,
            rowpad,
            colpad,
        )
        self.grid = TextureGrid.from_image_grid(image_grid)

    def check_cell(self, cell_texture, cellindex):
        self.assertTrue(cell_texture.width == self.grid.item_width)
        self.assertTrue(cell_texture.height == self.grid.item_height)

        color = colorbyte(cellindex + 1)
        cellimage = cell_texture.get_image_data()
        data = cellimage.get_bytes('R', cellimage.width)
        self.assertTrue(data == color * len(data))

    def setUp(self):
        self.w = Window(visible=False)

    def tearDown(self) -> None:
        self.w.close()

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

    def test_atlas_region_offset_preserved_for_multiple_border_sizes(self):
        image = ImageData(2, 2, "RGBA", bytes((255, 0, 0, 255)) * 4)

        for border in (0, 1, 2):
            atlas = TextureAtlas(width=16, height=16)
            region = atlas.add(image, border=border)
            grid = TextureGrid(region, rows=1, columns=1, item_width=2, item_height=2)
            cell = grid[0]

            self.assertEqual((cell.x, cell.y), (region.x, region.y))
            self.assertEqual(cell.tex_coords, region.tex_coords)

            fetched = bytes(cell.get_image_data().get_bytes("RGBA", cell.width * 4))
            self.assertEqual(fetched, bytes((255, 0, 0, 255)) * 4)

    def test_texture_region_input_preserves_region_coordinates(self):
        data = bytes(range(64))
        texture = ImageData(4, 4, "RGBA", data).get_texture()
        region = texture.get_region(1, 1, 2, 2)

        grid = TextureGrid(region, rows=1, columns=1, item_width=2, item_height=2)
        cell = grid[0]

        self.assertEqual((cell.x, cell.y), (region.x, region.y))
        self.assertEqual(cell.tex_coords, region.tex_coords)
        self.assertEqual(cell.get_image_data().get_bytes("RGBA", cell.width * 4),
                         region.get_image_data().get_bytes("RGBA", region.width * 4))
