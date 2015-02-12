#!/usr/bin/env python

"""
Test workaround for font missing metrics.

Font should fit between top and bottom lines.
"""

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import unittest

from pyglet.gl import *
from pyglet import font

from . import base_text

base_path = os.path.dirname(__file__)
test_data_path = os.path.abspath(os.path.join(base_path, '..', '..', 'data', 'fonts'))


class TEST_METRICS_WORKAROUND(base_text.TextTestBase):
    window_size = 600, 100

    def render(self):
        font.add_file(os.path.join(test_data_path, 'courR12-ISO8859-1.pcf'))

        fnt = font.load('Courier', 16)

        h = fnt.ascent - fnt.descent + 10
        self.texts = [
            font.Text(fnt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 10, h * 1),
        ]

    def draw(self):
        glPushAttrib(GL_CURRENT_BIT)

        for text in self.texts:
            text.draw()

            glBegin(GL_LINES)
            glColor3f(0, 1, 0)
            glVertex2f(text.x, text.y + text.font.descent)
            glVertex2f(text.x + text.width, text.y + text.font.descent)
            glColor3f(0, 0, 1)
            glVertex2f(text.x, text.y + text.font.ascent)
            glVertex2f(text.x + text.width, text.y + text.font.ascent)
            glEnd()
        glPopAttrib()

if __name__ == '__main__':
    unittest.main()
