#!/usr/bin/env python

'''Test rearrangement of color components using the OpenGL color matrix.
The test will be skipped if the GL_ARB_imaging extension is not present.

You should see the RGBA test image correctly rendered.  Press ESC to
end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load
import sys

from pyglet.gl import gl_info

class TEST_MATRIX_RGBA(base_load.TestLoad):
    texture_file = 'rgba.png'
    
    def load_image(self):
        if not gl_info.have_extension('GL_ARB_imaging'):
            print 'GL_ARB_imaging is not present, skipping test.'
            self.has_exit = True
        else:
            # Load image as usual then rearrange components
            super(TEST_PLATFORM_RGBA_LOAD, self).load_image()
            self.image.format = 'GBAR'
            pixels = self.image.data # forces conversion

if __name__ == '__main__':
    unittest.main()
