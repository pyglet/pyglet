#!/usr/bin/env python

'''Test L load using PyPNG.  You should see the l.png image on 
a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs.png import PNGImageDecoder

class TEST_PNG_L_LOAD(base_load.TestLoad):
    texture_file = 'l.png'
    decoder = PNGImageDecoder()

if __name__ == '__main__':
    unittest.main()
