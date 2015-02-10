#!/usr/bin/env python

'''Test DXT1 compressed RGB load from a DDS file.  You should see the
rgb_dxt1.dds image.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs.dds import DDSImageDecoder

class TEST_DDS_RGB_DXT1(base_load.TestLoad):
    texture_file = 'rgb_dxt1.dds'
    decoder = DDSImageDecoder()

if __name__ == '__main__':
    unittest.main()
