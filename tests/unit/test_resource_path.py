import os
import sys
from tests import mock
import unittest

from pyglet.resource import get_script_home, get_settings_path


_executable = os.path.abspath(os.path.join('path', 'exec'))
_script_home = os.path.abspath('path')


class ResourcePathTest(unittest.TestCase):
    """
    Test default paths returned for different platforms.
    """

    @mock.patch.object(sys, 'frozen', 'console_exe', create=True)
    @mock.patch.object(sys, 'executable', _executable)
    def test_script_home_frozen_console_exe(self):
        """Py2exe console executable"""
        self.assertEqual(get_script_home(), _script_home)

    @mock.patch.object(sys, 'frozen', 'windows_exe', create=True)
    @mock.patch.object(sys, 'executable', _executable)
    def test_script_home_frozen_windows_exe(self):
        """Py2exe windows executable"""
        self.assertEqual(get_script_home(), _script_home)

    @mock.patch.object(sys, 'frozen', 'macosx_app', create=True)
    @mock.patch.dict(os.environ, {'RESOURCEPATH': _script_home})
    def test_script_home_frozen_macosx(self):
        """Py2App OSX bundle"""
        self.assertEqual(get_script_home(), _script_home)

    @mock.patch.object(sys.modules['__main__'], '__file__', _executable)
    def test_script_home_normal_python(self):
        """Normal execution of a script in python."""
        self.assertEqual(get_script_home(), _script_home)

    @mock.patch.dict('sys.modules', {'__main__': None})
    @mock.patch.object(sys, 'executable', _executable)
    def test_script_home_cx_freeze(self):
        """Frozen binary created with cx_freeze"""
        self.assertEqual(get_script_home(), _script_home)

    @mock.patch('os.getcwd', return_value=_script_home)
    @mock.patch.dict('sys.modules', {'__main__': None})
    @mock.patch.object(sys, 'executable', 'python')
    def test_script_home_interactive(self, *_):
        """Interactive prompt, eg idle or cpython"""
        self.assertEqual(get_script_home(), _script_home)

