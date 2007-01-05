#!/usr/bin/env python

'''Test stencil buffer save.  

A scene consisting of a single coloured triangle will be rendered.  The
stencil buffer will then be saved to a stream and loaded as a texture.

You will see the original scene first for up to several seconds before the
stencil buffer image appears (because retrieving and saving the image is
a slow operation).  Messages will be printed to stdout indicating
what stage is occuring.
'''
__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from StringIO import StringIO
import unittest
import base_save

from pyglet.image import *
from pyglet.scene2d import *
from pyglet.window import *

class TEST_STENCIL_SAVE(base_save.TestSave):
    def draw_original(self):
        glClear(GL_STENCIL_BUFFER_BIT)

        glEnable(GL_STENCIL_TEST)
        glStencilFunc(GL_ALWAYS, 0xffffff, 0xffffff)
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
        return Window(width, height, visible=False, stencil_size=1)

    def load_texture(self):
        if self.window.get_config().get_gl_attributes()['stencil_size'] < 1:
            raise Exception('No stencil buffer')

        print 'Drawing scene...'
        self.window.set_visible()
        self.draw()

        print 'Saving stencil image...'
        glPixelTransferi(GL_INDEX_SHIFT, 7)
        image = StencilImage()
        file = StringIO()
        image.save('buffer.png', file)

        print 'Loading stencil image as texture...'
        file.seek(0)
        self.saved_texture = Image2d.load('buffer.png', file)

        print 'Done.'
        self.window.set_visible(False)

if __name__ == '__main__':
    unittest.main()
