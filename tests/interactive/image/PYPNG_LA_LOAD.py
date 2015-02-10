#!/usr/bin/env python

'''Test LA load using PyPNG.  You should see the la.png image on 
a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs.png import PNGImageDecoder

class TEST_PNG_LA_LOAD(base_load.TestLoad):
    texture_file = 'la.png'
    decoder = PNGImageDecoder()

if __name__ == '__main__':
    unittest.main()
