#!/usr/bin/env python

'''Test PNG RGB image load.  The image should have a black background,
not transparent.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load

class TEST_PNG_RGB_LOAD(base_load.TestLoad):
    texture_file = 'rgb.png'

if __name__ == '__main__':
    unittest.main()
