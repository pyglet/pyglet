#!/usr/bin/env python

'''Test LA save using PyPNG.  You should see la.png reference image
on the left, and saved (and reloaded) image on the right.  The saved image
may have larger dimensions due to texture size restrictions.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_save

from pyglet.image.codecs.png import PNGImageEncoder

class TEST_PNG_LA_SAVE(base_save.TestSave):
    texture_file = 'la.png'
    encoder = PNGImageEncoder()

if __name__ == '__main__':
    unittest.main()
