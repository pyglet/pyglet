#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.image import BufferImage

class ImageRegressionTestCase(unittest.TestCase):
    _enable_regression_image = False
    _captured_image = None

    def capture_regression_image(self):
        if not self._enable_regression_image:
            return False

        self._captured_image = BufferImage().get_raw_image()
        return True
