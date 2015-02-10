#!/usr/bin/env python

'''Test RGB save using PIL with no PNG encode available, next available
encoder will be used.  You should see rgb.png reference image on the left,
and saved (and reloaded) image on the right.  The saved image may have
larger dimensions due to texture size restrictions.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_save

from pyglet.image.codecs import ImageEncoder, ImageEncodeException
from pyglet.image.codecs.png import PNGImageEncoder
from pyglet.image import codecs

class MockPILImageEncoder(ImageEncoder):
    """Just raise an encode exception"""
    def encode(self, image, file, filename):
        raise ImageEncodeException("Encoder not available")

codecs.get_encoders = lambda filename: [MockPILImageEncoder(), PNGImageEncoder(),]

class TEST_NO_ENCODER_RGB_SAVE(base_save.TestSave):
    texture_file = 'rgb.png'
    encoder = None

if __name__ == '__main__':
    unittest.main()
