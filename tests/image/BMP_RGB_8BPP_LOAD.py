#!/usr/bin/env python

'''Test load using the Python BMP loader.  You should see the rgb_8bpp.bmp
image on a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs.bmp import BMPImageDecoder

class TEST_SUITE(base_load.TestLoad):
    texture_file = 'rgb_8bpp.bmp'
    decoder = BMPImageDecoder()

if __name__ == '__main__':
    unittest.main()
