from __future__ import absolute_import

import os
import unittest

from .future_test import FutureTestCase

local_dir = os.path.dirname(__file__)
test_data_path = os.path.abspath(os.path.join(local_dir, 'data'))
del local_dir

class PygletTestCase(FutureTestCase):
    """
    Base class for pyglet tests.
    Specifies helper methods for all tests.
    """
    @staticmethod
    def get_test_data_file(*file_parts):
        """
        Get a file from the test data directory in an OS independent way. Supply relative file
        name as you would in os.path.join().
        """
        return os.path.join(test_data_path, *file_parts)


class TestDataFixture(object):
    """Fixture for accessing test data."""
    def __init__(self):
        local_dir = os.path.dirname(__file__)
        self._test_data_path = os.path.abspath(os.path.join(local_dir, 'data'))

    def get_file(self, *file_parts):
        """
        Get a file from the test data directory in an OS independent way. Supply relative file
        name as you would in os.path.join().
        """
        return os.path.join(self._test_data_path, *file_parts)
