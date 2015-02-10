#!/usr/bin/env python

'''Test that a specific DPI can be set to render the text with.

Some text in Action Man font will be displayed.  A green box should exactly
bound the top and bottom of the text.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import os
import unittest

from pyglet.gl import *
from pyglet import font

from . import base_text

base_path = os.path.dirname(__file__)
test_data_path = os.path.abspath(os.path.join(base_path, '..', '..', 'data', 'fonts'))

class TEST_ADD_FONT(base_text.TextTestBase):
    font_name = 'Action Man'

    def render(self):
        font.add_file(os.path.join(test_data_path, 'action_man.ttf'))

        # Hard-code 16-pt at 100 DPI, and hard-code the pixel coordinates
        # we see that font at when DPI-specified rendering is correct.
        fnt = font.load('Action Man', 16, dpi=120)

        self.text = font.Text(fnt, 'The DPI is 120', 10, 10)

    def draw(self):
        self.text.draw()

        x1 = self.text.x
        x2 = self.text.x + self.text.width
        y1 = 9
        y2 = 27
        
        glPushAttrib(GL_CURRENT_BIT)
        glColor3f(0, 1, 0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1)
        glVertex2f(x2, y1)
        glVertex2f(x2, y2)
        glVertex2f(x1, y2)
        glEnd()
        glPopAttrib()

if __name__ == '__main__':
    unittest.main()
