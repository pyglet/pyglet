import unittest
from tests import mock
import imp
import pyglet
import warnings


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

    @mock.patch('sys.platform', 'darwin')
    @mock.patch('platform.mac_ver', lambda: ['10.5.0'])
    @mock.patch('struct.calcsize', lambda i: 4)
    def test_carbon_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as warning_catcher:
            warnings.simplefilter('always')

            # Reset the warning registry
            # By default deprecation warnings are ignored. If the warning has already been
            # raised earlier, the registry prevents it from showing again, even if the filter
            # is set to allow it.
            if hasattr(pyglet, '__warningregistry__'):
                del pyglet.__warningregistry__

            imp.reload(pyglet)

            self.assertEqual(pyglet.options['darwin_cocoa'], False)
            self.assertEqual(len(warning_catcher), 1)
            self.assertIs(warning_catcher[-1].category, PendingDeprecationWarning)
            self.assertIn('deprecated', str(warning_catcher[-1].message))

