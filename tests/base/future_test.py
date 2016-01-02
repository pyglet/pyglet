from builtins import bytes
import sys
import unittest

if sys.version_info[:2] < (3, 0):
    _py2 = True
else:
    _py2 = False


class FutureTestCase(unittest.TestCase):
    """Base class for unittests that adds compatibility for both the Py2 and Py3 version of the
    unittest module."""

    if _py2:
        assertCountEqual = unittest.TestCase.assertItemsEqual

    if _py2:
        assertBytesEqual = unittest.TestCase.assertEqual
    else:
        def assertBytesEqual(self, first, second, msg=None):
            if isinstance(first, str):
                first = first.encode('latin-1')
            elif not isinstance(first, bytes):
                first = bytes(first)
            if isinstance(second, str):
                second = second.encode('latin-1')
            elif not isinstance(second, bytes):
                second = bytes(second)
            self.assertEqual(first, second)
