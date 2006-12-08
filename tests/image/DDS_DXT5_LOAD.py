#!/usr/bin/env python

'''Test DDS DXT5 image load.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load

from pyglet.image.codecs import *
from pyglet.image.codecs import dds

class TEST_DDS_DXT5_LOAD(base_load.TestLoad):
    texture_file = 'dxt5.dds'

    def choose_codecs(self):
        clear_decoders()
        add_decoders(dds)

if __name__ == '__main__':
    unittest.main()
