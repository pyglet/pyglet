#!/usr/bin/env python

'''Test RGBA save using PyPNG.  You should see rgba.png reference image
on the left, and saved (and reloaded) image on the right.  The saved image
may have larger dimensions due to texture size restrictions.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_save

from pyglet.image.codecs import *
from pyglet.image.codecs import png

class TEST_PNG_RGBA_SAVE(base_save.TestSave):
    texture_file = 'rgba.png'

    def choose_codecs(self):
        clear_encoders()
        add_encoders(png)

if __name__ == '__main__':
    unittest.main()
