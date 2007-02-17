#!/usr/bin/env python

'''Test RGB load using PyPNG.  You should see the rgb.png image on 
a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load

from pyglet.image.codecs.png import PNGImageDecoder

class TEST_PNG_RGB_LOAD(base_load.TestLoad):
    texture_file = 'rgb.png'
    decoder = PNGImageDecoder()

if __name__ == '__main__':
    unittest.main()
