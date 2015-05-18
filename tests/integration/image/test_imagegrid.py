from __future__ import absolute_import
from builtins import range
import unittest

from pyglet.gl import *
from pyglet.image import *
from pyglet.window import *

from .texture_compat import colorbyte

class ImageGridTestCase(unittest.TestCase):
    """Test the ImageGrid for textures."""
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
        self.image = ImageData(width, height, 'L', data)
        self.grid = ImageGrid(self.image, rows, cols,
            itemwidth, itemheight, rowpad, colpad).texture_sequence

    def check_cell(self, cellimage, cellindex):
        self.assertTrue(cellimage.width == self.grid.item_width)
        self.assertTrue(cellimage.height == self.grid.item_height)

        color = colorbyte(cellindex + 1)
        cellimage = cellimage.image_data
        data = cellimage.get_data('L', cellimage.width)
        self.assertTrue(data == color * len(data))

    def setUp(self):
        self.w = Window(visible=False)

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
        images = self.grid[(3,2):(6,5)]
        i = 0
        for row in range(3,6):
            for col in range(2,5):
                self.check_cell(images[i], row * cols + col)
                i += 1

