#!/usr/bin/env python

'''Test that font.Text alignment works with multiple lines.

Three labels will be rendered at the top-left, center and bottom-right of the
window.  Resize the window to ensure the alignment is as specified.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import font

from . import base_text

class TEST_ALIGN_MULTILINE(base_text.TextTestBase):
    font_name = ''
    window_size = 400, 500

    def render(self):
        fnt = font.load(self.font_name, self.font_size)

        w = self.window.width
        h = self.window.height

        self.labels = [
            font.Text(fnt, 
                'This text is top-left aligned  with several lines.', 
                0, h, width=w, 
                halign='left', valign='top'),
            font.Text(fnt, 
                'This text is centered in the middle.',
                0, h//2, width=w, 
                halign='center', valign='center'),
            font.Text(fnt, 
                'This text is aligned to the bottom-right of the window.',
                0, 0, width=w, 
                halign='right', valign='bottom'),
        ]

    def on_resize(self, width, height):
        for label in self.labels:
            label.width = width
        self.labels[0].y = height
        self.labels[1].y = height // 2

    def draw(self):
        for label in self.labels:
            label.draw()

if __name__ == '__main__':
    unittest.main()
