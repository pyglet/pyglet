import unittest

from pyglet.image import ImageData, ImageGrid
from pyglet.window import Window


def colorbyte(color):
    return bytes((color,))


class ImageGridTestCase(unittest.TestCase):
    """Test the ImageGrid for textures."""

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
        self.grid = ImageGrid(self.image, rows, cols,
                              item_width, item_height, rowpad, colpad).get_texture_sequence()

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

    def testPad(self):
        # Test a 5x3 grid with rowpad=3 and colpad=7 and 10x9 images
        rows, cols = 5, 3
        self.set_grid_image(10, 9, rows, cols, 3, 7)
        for i in range(rows * cols):
            self.check_cell(self.grid[i], i)

    def testTuple(self):
        # Test tuple access
        rows, cols = 3, 4
        self.set_grid_image(5, 5, rows, cols, 0, 0)
        for row in range(rows):
            for col in range(cols):
                self.check_cell(self.grid[(row, col)], row * cols + col)

    def testRange(self):
        # Test range access
        rows, cols = 4, 3
        self.set_grid_image(10, 1, rows, cols, 0, 0)
        images = self.grid[4:8]
        for i, image in enumerate(images):
            self.check_cell(image, i + 4)

    def testTupleRange(self):
        # Test range over tuples
        rows, cols = 10, 10
        self.set_grid_image(4, 4, rows, cols, 0, 0)
        images = self.grid[(3, 2):(6, 5)]
        i = 0
        for row in range(3, 6):
            for col in range(2, 5):
                self.check_cell(images[i], row * cols + col)
                i += 1
