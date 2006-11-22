#!/usr/bin/env python

'''Test L load using PyPNG.  You should see the l.png image on 
a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs import *
from pyglet.image.codecs import png

class TEST_L_RGBA_LOAD(base_load.TestLoad):
    texture_file = 'l.png'

    def choose_codecs(self):
        clear_decoders()
        add_decoders(png)

if __name__ == '__main__':
    unittest.main()
