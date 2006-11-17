#!/usr/bin/env python

'''Test PNG RGBA image save.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_save

class TEST_PNG_RGBA_SAVE(base_save.TestSave):
    texture_file = 'rgb.png'

if __name__ == '__main__':
    unittest.main()
