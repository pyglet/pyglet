#!/usr/bin/env python

'''Test RGB load using the platform decoder (QuickTime, Quartz, GDI+ or Gdk).
You should see the rgb.png image on a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load
import sys

if sys.platform == 'linux2':
    from pyglet.image.codecs.gdkpixbuf2 import GdkPixbuf2ImageDecoder as dclass
elif sys.platform in ('win32', 'cygwin'):
    from pyglet.image.codecs.gdiplus import GDIPlusDecoder as dclass
elif sys.platform == 'darwin':
    from pyglet import options as pyglet_options
    if pyglet_options['darwin_cocoa']:
        from pyglet.image.codecs.quartz import QuartzImageDecoder as dclass
    else:
        from pyglet.image.codecs.quicktime import QuickTimeImageDecoder as dclass

class TEST_PLATFORM_RGB_LOAD(base_load.TestLoad):
    texture_file = 'rgb.png'
    decoder = dclass()

if __name__ == '__main__':
    unittest.main()
