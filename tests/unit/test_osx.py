import unittest
import mock
import imp
import pyglet


class OSXImportTestCase(unittest.TestCase):

    @mock.patch("sys.platform", "darwin")
    @mock.patch("platform.mac_ver", lambda: ['10.5.0'])
    def test_cannot_import_old_osx(self):
        with self.assertRaises(Exception) as e:
            imp.reload(pyglet)

    @mock.patch("sys.platform", "darwin")
    @mock.patch('struct.calcsize', lambda i: 4)
    @mock.patch("platform.mac_ver", lambda: ['10.10.0'])
    def test_cannot_import_32bit_python(self):
        with self.assertRaises(Exception) as e:
            imp.reload(pyglet)

    @mock.patch("sys.platform", "darwin")
    @mock.patch("platform.mac_ver", lambda: ['10.6.0'])
    def test_can_import_osx_current_version(self):
        imp.reload(pyglet)
