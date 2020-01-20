import unittest


# TODO: remove this legacy base class
class FutureTestCase(unittest.TestCase):
    """Base class for unittests that adds compatibility for both the Py2 and Py3 version of the
    unittest module."""

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

