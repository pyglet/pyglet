#!/usr/bin/env python

'''Test that a font distributed with the application can be displayed.

Four lines of text should be displayed, each in a different variant
(bold/italic/regular) of Action Man at 24pt.  The Action Man fonts are
included in the test data directory (tests/data/fonts) as action_man*.ttf.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import os
import unittest

from pyglet import font

from . import base_text

base_path = os.path.dirname(__file__)
test_data_path = os.path.abspath(os.path.join(base_path, '..', '..', 'data', 'fonts'))

class TEST_ADD_FONT(base_text.TextTestBase):
    font_name = 'Action Man'

    def render(self):
        font.add_file(os.path.join(test_data_path, 'action_man.ttf'))
        font.add_file(os.path.join(test_data_path, 'action_man_bold.ttf'))
        font.add_file(os.path.join(test_data_path, 'action_man_italic.ttf'))
        font.add_file(os.path.join(test_data_path, 'action_man_bold_italic.ttf'))

        fnt = font.load('Action Man', self.font_size)
        fnt_b = font.load('Action Man', self.font_size, bold=True)
        fnt_i = font.load('Action Man', self.font_size, italic=True)
        fnt_bi = font.load('Action Man', self.font_size, bold=True, italic=True)

        h = fnt.ascent - fnt.descent

        self.labels = [
            font.Text(fnt, 'Action Man', 10, 10 + 3 * h),
            font.Text(fnt_i, 'Action Man Italic', 10, 10 + 2 * h),
            font.Text(fnt_b, 'Action Man Bold', 10, 10 + h),
            font.Text(fnt_bi, 'Action Man Bold Italic', 10, 10)
        ]

    def draw(self):
        for label in self.labels:
            label.draw()

if __name__ == '__main__':
    unittest.main()
