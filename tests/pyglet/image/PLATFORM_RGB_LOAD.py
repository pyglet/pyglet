#!/usr/bin/env python

'''Test RGB load using the platform decoder (QuickTime, GDI+ or Gdk).  You
should see the rgb.png image on a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load
import sys

from pyglet.image.codecs import *

if sys.platform == 'linux2':
    from pyglet.image.codecs import gdkpixbuf2 as platform_decoder
elif sys.platform == 'win32':
    from pyglet.image.codecs import gdiplus as platform_decoder
elif sys.platform == 'darwin':
    from pyglet.image.codecs import quicktime as platform_decoder

class TEST_PNG_RGB_LOAD(base_load.TestLoad):
    texture_file = 'rgb.png'

    def choose_codecs(self):
        clear_decoders()
        add_decoders(platform_decoder)

if __name__ == '__main__':
    unittest.main()
