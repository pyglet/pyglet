import os
import re
import sys
import unittest
from unittest import mock

import pyglet
from pyglet.resource import get_script_home, get_settings_path


_executable = os.path.abspath(os.path.join('path', 'exec'))
_script_home = os.path.abspath('path')


def _mock_expand_user(p):
    parts = re.split(r"[\\/]+", p)
    parts[0] = 'pyglet'
    return os.path.join(*parts)


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


    @mock.patch.object(pyglet, 'compat_platform', 'cygwin')
    @mock.patch.dict('os.environ', {'APPDATA': 'pyglet'})
    def test_settings_path_cygwin_appdata(self):
        """Settings path on cygwin with APPDATA set."""
        self.assertEqual(get_settings_path('myapp'),
                         os.path.join('pyglet', 'myapp'))

    @mock.patch.object(pyglet, 'compat_platform', 'win32')
    @mock.patch.dict('os.environ', {'APPDATA': 'pyglet'})
    def test_settings_path_windows_appdata(self):
        """Settings path on cygwin with APPDATA set."""
        self.assertEqual(get_settings_path('myapp'),
                         os.path.join('pyglet', 'myapp'))

    @mock.patch.object(pyglet, 'compat_platform', 'cygwin')
    @mock.patch.object(os, 'environ', {})
    @mock.patch.object(os.path, 'expanduser', _mock_expand_user)
    def test_settings_path_cygwin_no_appdata(self):
        """Settings path on cygwin without APPDATA set."""
        self.assertEqual(get_settings_path('myapp'),
                         os.path.join('pyglet', 'myapp'))

    @mock.patch.object(pyglet, 'compat_platform', 'win32')
    @mock.patch.object(os, 'environ', {})
    @mock.patch.object(os.path, 'expanduser', _mock_expand_user)
    def test_settings_path_windows_no_appdata(self):
        """Settings path on cygwin without APPDATA set."""
        self.assertEqual(get_settings_path('myapp'),
                         os.path.join('pyglet', 'myapp'))

    @mock.patch.object(pyglet, 'compat_platform', 'darwin')
    @mock.patch.object(os.path, 'expanduser', _mock_expand_user)
    def test_settings_path_darwin(self):
        """Settings path on OSX."""
        self.assertEqual(get_settings_path('myapp'),
                         os.path.join('pyglet', 'Library', 'Application Support', 'myapp'))

    @mock.patch.object(pyglet, 'compat_platform', 'linux')
    @mock.patch.dict('os.environ', {'XDG_CONFIG_HOME': 'pyglet'})
    def test_settings_path_linux_xdg_config_home(self):
        """Settings path on Linux with XDG_CONFIG_HOME available."""
        self.assertEqual(get_settings_path('myapp'),
                         os.path.join('pyglet', 'myapp'))

    @mock.patch.object(pyglet, 'compat_platform', 'linux')
    @mock.patch.object(os, 'environ', {})
    @mock.patch.object(os.path, 'expanduser', _mock_expand_user)
    def test_settings_path_linux_xdg_config_home(self):
        """Settings path on Linux without XDG_CONFIG_HOME."""
        self.assertEqual(get_settings_path('myapp'),
                         os.path.join('pyglet', '.config', 'myapp'))

