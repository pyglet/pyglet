#!/usr/bin/env python

'''Test that text will not wrap when its width is set to its calculated
width.

You should be able to clearly see "TEST TEST" on a single line.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest
import base_text

class TEST_WRAPPING(base_text.TextTestBase):
    font_name = ''
    text = 'TEST TEST'

    def render(self):
        super(TEST_WRAPPING, self).render()
        self.label.width = self.label.width

    def draw(self):
        self.label.draw()

if __name__ == '__main__':
    unittest.main()
