#!/usr/bin/env python

'''Test L load using the platform decoder (QuickTime, Quartz, GDI+ or Gdk).
You should see the l.png image on a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load
from pyglet import compat_platform

if compat_platform.startswith('linux'):
    from pyglet.image.codecs.gdkpixbuf2 import GdkPixbuf2ImageDecoder as dclass
elif compat_platform in ('win32', 'cygwin'):
    from pyglet.image.codecs.gdiplus import GDIPlusDecoder as dclass
elif compat_platform == 'darwin':
    from pyglet import options as pyglet_options
    if pyglet_options['darwin_cocoa']:
        from pyglet.image.codecs.quartz import QuartzImageDecoder as dclass
    else:
        from pyglet.image.codecs.quicktime import QuickTimeImageDecoder as dclass

class TEST_PLATFORM_L_LOAD(base_load.TestLoad):
    texture_file = 'l.png'
    decoder = dclass()

if __name__ == '__main__':
    unittest.main()
