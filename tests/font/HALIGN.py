#!/usr/bin/env python

'''Test that font.Label horizontal alignment works.

Three labels will be rendered aligned left, center and right.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import font

import base_text

class TEST_HALIGN(base_text.TextTestBase):
    font_name = ''

    def render(self):
        fnt = font.load('', self.font_size)

        h = fnt.ascent - fnt.descent
        w = self.window.width

        self.labels = [
            font.Label(fnt, 'LEFT', 0, 10 + 3 * h, width=w, halign='left'),
            font.Label(fnt, 'CENTER', 0, 10 + 2 * h, width=w, halign='center'),
            font.Label(fnt, 'RIGHT', 0, 10 + h, width=w, halign='right'),
        ]

    def draw(self):
        for label in self.labels:
            label.draw()

if __name__ == '__main__':
    unittest.main()
