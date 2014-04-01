#!/usr/bin/env python

'''Test load using the Python gdkpixbuf2 GIF loader.  You should see the 8bpp.gif
image on a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs.gdkpixbuf2 import GdkPixbuf2ImageDecoder

class TEST_GIF_LOAD(base_load.TestLoad):
    texture_file = '8bpp.gif'
    decoder = GdkPixbuf2ImageDecoder()

if __name__ == '__main__':
    unittest.main()
