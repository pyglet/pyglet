#!/usr/bin/env python

'''Test that a font likely to be installed on the computer can be
loaded and displayed correctly.

One window will open, it should show "Quickly brown fox" at 24pt using:

  * "Helvetica" on Mac OS X
  * "Arial" on Windows

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import sys
from . import base_text

if sys.platform == 'darwin':
    font_name = 'Helvetica'
elif sys.platform in ('win32', 'cygwin'):
    font_name = 'Arial'
else:
    font_name = 'Arial'

class TEST_SYSTEM(base_text.TextTestBase):
    font_name = font_name
    font_size = 24

if __name__ == '__main__':
    unittest.main()
