import unittest
import mock
import imp
import pyglet


class OSXImportTestCase(unittest.TestCase):

    @mock.patch('sys.platform', 'darwin')
    @mock.patch('platform.mac_ver', lambda: ['10.5.0'])
    @mock.patch('struct.calcsize', lambda i: 4)
    def test_old_32bit_osx_uses_carbon(self):
        imp.reload(pyglet)
        self.assertEqual(pyglet.options['darwin_cocoa'], False)

    @mock.patch("sys.platform", "darwin")
    @mock.patch("platform.mac_ver", lambda: ['10.5.0'])
    @mock.patch('struct.calcsize', lambda i: 8)
    def test_old_64bit_osx_not_supported(self):
        with self.assertRaises(Exception) as e:
            imp.reload(pyglet)

    @mock.patch("sys.platform", "darwin")
    @mock.patch('struct.calcsize', lambda i: 4)
    @mock.patch("platform.mac_ver", lambda: ['10.10.0'])
    def test_32bit_osx_uses_carbon(self):
        imp.reload(pyglet)
        self.assertEqual(pyglet.options['darwin_cocoa'], False)

    @mock.patch("sys.platform", "darwin")
    @mock.patch("platform.mac_ver", lambda: ['10.6.0'])
    @mock.patch('struct.calcsize', lambda i: 8)
    def test_64bit_osx_uses_cocoa(self):
        imp.reload(pyglet)
        self.assertEqual(pyglet.options['darwin_cocoa'], True)
