#!/usr/bin/env python

'''Test buffer save.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import StringIO
import unittest
import base_save

from pyglet.image import *

class TEST_BUFFER_SAVE(base_save.TestSave):
    def draw_original(self):
        glBegin(GL_TRIANGLES)
        glColor4f(1, 0, 0, 1)
        glVertex3f(0, 0, -1)
        glColor4f(0, 1, 0, 1)
        glVertex3f(200, 0, 0)
        glColor4f(0, 0, 1, 1)
        glVertex3f(0, 200, 1)
        glEnd()

        glColor4f(1, 1, 1, 1)

    def load_texture(self):
        self.window.set_visible()
        self.draw()

        image = BufferImage()
        file = StringIO.StringIO()
        image.save('buffer.png', file)
        file.seek(0)
        self.saved_texture = Texture.load('buffer.png', file)

        self.window.set_visible(False)

if __name__ == '__main__':
    unittest.main()
