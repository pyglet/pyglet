#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.image import get_buffer_manager

class ImageRegressionTestCase(unittest.TestCase):
    _enable_regression_image = False
    _enable_interactive = True
    _captured_image = None

    def capture_regression_image(self):
        if not self._enable_regression_image:
            return False

        self._captured_image = \
            get_buffer_manager().get_color_buffer().image_data
        return not self._enable_interactive
