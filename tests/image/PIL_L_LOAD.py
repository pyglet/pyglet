#!/usr/bin/env python

'''Test L load using PIL.  You should see the la.png image on 
a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs.pil import *

class TEST_PIL_L(base_load.TestLoad):
    texture_file = 'l.png'
    decoder = PILImageDecoder()

if __name__ == '__main__':
    unittest.main()
