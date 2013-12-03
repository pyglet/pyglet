#!/usr/bin/env python

'''Test RGB load using PIL, decoder is not available and PYPNG decoder
is used.  You should see the rgb.png image on a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load

from pyglet.image.codecs.pil import Image, PILImageDecoder
from pyglet.image.codecs.png import PNGImageDecoder
from pyglet.image import codecs

def raise_error(obj, param):
    raise Exception()
Image.Image.transpose = raise_error

codecs.get_decoders = lambda filename: [PILImageDecoder(), PNGImageDecoder(),]

class TEST_PIL_RGB_LOAD_NO_DECODER(base_load.TestLoad):
    texture_file = 'rgb.png'
    decoder = None

if __name__ == '__main__':
    unittest.main()
