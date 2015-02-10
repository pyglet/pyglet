#!/usr/bin/env python

'''Test that window icon can be set for multiple sizes.

Expected behaviour:
    One window will be opened.  The window's icon depends on the icon
    size:

      16x16 icon is a yellow "1"
      32x32 icon is a purple "2"
      48x48 icon is a cyan "3"
      72x72 icon is a red "4"
      128x128 icon is a blue "5"

    For other sizes, the operating system may select the closest match and
    scale it (Linux, Windows), or interpolate between two or more images
    (Mac OS X).

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: WINDOW_SET_MOUSE_CURSOR.py 717 2007-03-03 07:04:10Z Alex.Holkner $'

import unittest

from pyglet.gl import *
from pyglet import image
from pyglet import window
from pyglet.window import key

import window_util

from os.path import abspath, join, dirname
test_data_path = abspath(join(dirname(__file__), '..', '..', 'data', 'images'))
icon_file1 = join(test_data_path, 'icon_size1.png')
icon_file2 = join(test_data_path, 'icon_size2.png')
icon_file3 = join(test_data_path, 'icon_size3.png')
icon_file4 = join(test_data_path, 'icon_size4.png')
icon_file5 = join(test_data_path, 'icon_size5.png')

class WINDOW_SET_ICON_SIZES(unittest.TestCase):
    def test_set_icon_sizes(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height)
        w.set_icon(image.load(icon_file1),
                   image.load(icon_file2),
                   image.load(icon_file3),
                   image.load(icon_file4),
                   image.load(icon_file5))
        glClearColor(1, 1, 1, 1)
        while not w.has_exit:
            glClear(GL_COLOR_BUFFER_BIT)
            w.flip()
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
