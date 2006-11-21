#!/usr/bin/env python

'''Test depth save.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import StringIO
import unittest
import base_save

from pyglet.image import *

class TEST_DEPTH_SAVE(base_save.TestSave):
    def draw_original(self):
        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glBegin(GL_TRIANGLES)
        glColor4f(1, 0, 0, 1)
        glVertex3f(0, 0, -1)
        glColor4f(0, 1, 0, 1)
        glVertex3f(200, 0, 0)
        glColor4f(0, 0, 1, 1)
        glVertex3f(0, 200, 1)
        glEnd()

        glDisable(GL_DEPTH_TEST)
        glColor4f(1, 1, 1, 1)

    def load_texture(self):
        self.window.set_visible()
        self.draw()

        image = DepthImage()
        file = StringIO.StringIO()
        image.save('buffer.png', file)
        file.seek(0)
        self.saved_texture = Texture.load('buffer.png', file)

        self.window.set_visible(False)

if __name__ == '__main__':
    unittest.main()
