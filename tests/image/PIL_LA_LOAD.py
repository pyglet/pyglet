#!/usr/bin/env python

'''Test LA load using PIL.  You should see the la.png image on 
a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs import *
from pyglet.image.codecs import pil

class TEST_PNG_LA(base_load.TestLoad):
    texture_file = 'la.png'

    def choose_codecs(self):
        clear_decoders()
        add_decoders(pil)

if __name__ == '__main__':
    unittest.main()
