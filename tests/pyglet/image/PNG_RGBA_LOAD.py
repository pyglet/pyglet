#!/usr/bin/env python

'''Test PNG RGBA image load.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_load

class TEST_PNG_RGBA_LOAD(base_load.TestLoad):
    texture_file = 'rgba.png'

if __name__ == '__main__':
    unittest.main()
