#!/usr/bin/env python

'''Test that the horizontal font metrics are calculated correctly.

Some text in various fonts will be displayed.  Green vertical lines mark
the left edge of the text.  Blue vertical lines mark the right edge of the
text.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import unittest

from pyglet.gl import *
from pyglet import font

from . import base_text

base_path = os.path.dirname(__file__)
test_data_path = os.path.abspath(os.path.join(base_path, '..', 'data', 'fonts'))

class TEST_HORIZONTAL_METRICS(base_text.TextTestBase):
    window_size = 400, 250

    def render(self):
        font.add_file(os.path.join(test_data_path, 'action_man.ttf'))

        fnt1 = font.load('Action Man', 16)
        fnt2 = font.load('Arial', 16)
        fnt3 = font.load('Times New Roman', 16)

        h = fnt3.ascent - fnt3.descent + 10
        self.texts = [
            font.Text(fnt1, 'Action Man', 10, h * 1),
            font.Text(fnt1, 'Action Man longer test with more words', 10, h*2),
            font.Text(fnt2, 'Arial', 10, h * 3),
            font.Text(fnt2, 'Arial longer test with more words', 10, h*4),
            font.Text(fnt3, 'Times New Roman', 10, h * 5),
            font.Text(fnt3, 'Times New Roman longer test with more words', 
                      10, h*6),
        ]

    def draw(self):
        glPushAttrib(GL_CURRENT_BIT)

        for text in self.texts:
            text.draw()

            glBegin(GL_LINES)
            glColor3f(0, 1, 0)
            glVertex2f(text.x, text.y + text.font.descent)
            glVertex2f(text.x, text.y + text.font.ascent)
            glColor3f(0, 0, 1)
            glVertex2f(text.x + text.width, text.y + text.font.descent)
            glVertex2f(text.x + text.width, text.y + text.font.ascent)
            glEnd()
        glPopAttrib()

if __name__ == '__main__':
    unittest.main()
