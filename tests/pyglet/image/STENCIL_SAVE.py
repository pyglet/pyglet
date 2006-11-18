#!/usr/bin/env python

'''Test stencil save.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import StringIO
import unittest
import base_save

from pyglet.image import *
import pyglet.window

class TEST_STENCIL_SAVE(base_save.TestSave):
    def draw_original(self):
        glClear(GL_STENCIL_BUFFER_BIT)

        glEnable(GL_STENCIL_TEST)
        glStencilFunc(GL_ALWAYS, 1, 0xffffff)
        glStencilOp(GL_REPLACE, GL_REPLACE, GL_REPLACE)

        glBegin(GL_TRIANGLES)
        glColor4f(1, 0, 0, 1)
        glVertex3f(0, 0, -1)
        glColor4f(0, 1, 0, 1)
        glVertex3f(200, 0, 0)
        glColor4f(0, 0, 1, 1)
        glVertex3f(0, 200, 1)
        glEnd()

        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glDisable(GL_STENCIL_TEST)

        glColor4f(1, 1, 1, 1)

    def create_window(self):
        width, height = 400, 400
        return pyglet.window.create(width, height, visible=False, 
            stencil_size=1)

    def load_texture(self):
        self.window.set_visible()

        glPixelTransferi(GL_INDEX_SHIFT, 7)
        image = StencilImage()
        file = StringIO.StringIO()
        image.save('buffer.png', file)
        file.seek(0)
        self.saved_texture = Texture.load('buffer.png', file)

        self.window.set_visible(False)

if __name__ == '__main__':
    unittest.main()
