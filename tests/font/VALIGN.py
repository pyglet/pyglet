#!/usr/bin/env python

'''Test that font.Text vertical alignment works.

Four labels will be aligned top, center, baseline and bottom.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import gl
from pyglet import font

from . import base_text

class TEST_VALIGN(base_text.TextTestBase):
    font_name = ''
    window_size = 600, 200

    def render(self):
        fnt = font.load('', self.font_size)

        h = fnt.ascent - fnt.descent
        w = self.window.width

        self.labels = []
        x = 0
        for align in 'top center baseline bottom'.split():
            label = align.upper() + 'y'
            self.labels.append(font.Text(fnt, label, x, 50, valign=align))
            x += self.labels[-1].width

    def draw(self):
        gl.glColor3f(1, 1, 1)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(0, 50)
        gl.glVertex2f(self.window.width, 50)
        gl.glEnd()

        for label in self.labels:
            label.draw()

if __name__ == '__main__':
    unittest.main()
