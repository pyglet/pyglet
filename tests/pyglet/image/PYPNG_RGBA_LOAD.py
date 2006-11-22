#!/usr/bin/env python

'''Test RGBA load using PyPNG.  You should see the rgba.png image on 
a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load

from pyglet.image.codecs import *
from pyglet.image.codecs import png

class TEST_PNG_RGBA_LOAD(base_load.TestLoad):
    texture_file = 'rgba.png'

    def choose_codecs(self):
        clear_decoders()
        add_decoders(png)

if __name__ == '__main__':
    unittest.main()
