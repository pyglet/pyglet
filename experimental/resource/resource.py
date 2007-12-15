#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import os
import zipfile
import StringIO

from pyglet import font
from pyglet import image

class ResourceNotFoundException(Exception):
    '''The named resource was not found on the search path.'''
    def __init__(self, name):
        message = ('Resource "%s" was not found on the path.  '
            'Ensure that the filename has the correct captialisation.') % name
        super(ResourceNotFoundException, self).__init__(message)

def get_script_home():
    '''Get the directory containing the program entry module.

    For ordinary Python scripts, this is the directory containing the
    ``__main__`` module.  For executables created with py2exe the result is
    the directory containing the running executable file.  For OS X bundles
    created using Py2App the result is the Resources directory within the
    running bundle.

    If none of the above cases apply and the file for ``__main__`` cannot
    be determined the working directory is returned.

    :rtype: str
    '''

    frozen = getattr(sys, 'frozen', None)
    if frozen in ('windows_exe', 'console_exe'):
        return os.path.dirname(sys.executable)
    elif frozen == 'macosx_app':
        return os.environ['RESOURCEPATH']
    else:
        main = sys.modules['__main__']
        if hasattr(main, '__file__'):
            return os.path.dirname(main.__file__)

    # Probably interactive
    return ''

class Loader(object):
    '''Load program resource files from disk.

    The loader contains a search path which can include filesystem
    directories, ZIP archives and Python packages.
    '''
    def __init__(self, path=None, script_home=None):
        '''Create a loader for the given path.

        The path is a list of locations to search for resources.  Locations
        are searched in the order given in the path.  If a location is not
        valid (for example, if the directory does not exist), it is skipped.

        Locations in the path beginning with an ampersand (''@'' symbol)
        specify Python packages.  Other locations specify a ZIP archive
        or directory on the filesystem.  Locations that are not absolute
        are assumed to be relative to the script home.

        Paths are always case-sensitive, even if the filesystem is not.  This
        avoids a common error when porting applications between platforms.

        If no path is specified it defaults to ``['.', '@__main__']``; that
        is, the program directory is searched first, followed by the package
        directory of the entry module.

        :Parameters:
            `path` : list of str
                List of locations to search for resources.
            `script_home` : str
                Root of relative locations; defaults to the result of 
                `get_script_home`.

        '''
        if path is None:
            path = ['.', '@__main__']
        if type(path) in (str, unicode):
            path = [path]
        self.path = list(path)
        if script_home is None:
            script_home = get_script_home()
        self.script_home = script_home
        self.reindex()

    def reindex(self):
        '''Refresh the file index.

        You must call this method if `path` is changed or the filesystem
        layout changes.
        '''
        self._index = {}
        for path in self.path:
            # Module
            if path.startswith('@'):
                try:
                    module = __import__(path[1:])
                    path = module.__file__
                except:
                    continue

            # Add script base unless absolute
            if not os.path.isabs(path):
                assert '\\' not in path, \
                    'Backslashes not permitted in relative path'
                path = os.path.join(self.script_home, path)

            if os.path.isdir(path):
                # Filesystem directory
                for name in os.listdir(path):
                    self._index_file(name, open, os.path.join(path, name))
            else:
                # Find path component that is the ZIP file.
                dir = ''
                while path and not os.path.isfile(path):
                    path, tail_dir = os.path.split(path)
                    dir = os.path.join(tail_dir, dir)
                dir = dir.rstrip('/')

                # path is a ZIP file, dir resides within ZIP
                if path and zipfile.is_zipfile(path):
                    zip = zipfile.ZipFile(path, 'r')
                    zip_open = (lambda z: lambda name, mode:
                        StringIO.StringIO(z.read(name)))(zip)
                    for name_path in zip.namelist():
                        name_dir, name = os.path.split(name_path)
                        assert '\\' not in name_dir
                        assert not name_dir.endswith('/')
                        if name_dir == dir:
                            self._index_file(name, zip_open, name_path)

    def _index_file(self, name, func, path):
        if name not in self._index:
            self._index[name] = (func, path)

    def file(self, name, mode='rb'):
        '''Load a resource.

        :Parameters:
            `name` : str
                Filename of the resource to load.
            `mode` : str
                Combination of ``r``, ``w``, ``a``, ``b`` and ``t`` characters
                with the meaning as for the builtin ``open`` function.

        :rtype: file object
        '''
        try:
            func, path = self._index[name]
            return func(path, mode)
        except KeyError:
            raise ResourceNotFoundException(name)
