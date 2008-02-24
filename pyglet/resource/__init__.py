#!/usr/bin/env python

'''Load application resources from a known path.

Loading resources by specifying relative paths to filenames is often
problematic in Python, as the working directory is not necessarily the same
directory as the application's script files.

This module allows applications to specify a search path for resources.
Relative paths are taken to be relative to the application's __main__ module.
ZIP files can appear on the path; they will be searched inside.  The resource
module also behaves as expected when applications are bundled using py2exe or
py2app.

By default, the search path `path` for resources includes the location of the
application's ``__main__`` module and the current working directory.  This
allows users or developers to easily override specific resources by adding
newer files to the working directory.  The path is a list of locations to
search and can be modified directly.  After modifying the path, call
`reindex`.

As well as providing file references (with the `file` function), the resource
module also contains convenience functions for loading images, textures,
fonts, media and documents.

3rd party modules or packages not bound to a specific application should
construct their own `Loader` instance and override the path to use the
resources in the module's directory.

:since: pyglet 1.1
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import operator
import os
import sys
import zipfile
import StringIO

import pyglet

class ResourceNotFoundException(Exception):
    '''The named resource was not found on the search path.'''
    def __init__(self, name):
        message = ('Resource "%s" was not found on the path.  '
            'Ensure that the filename has the correct captialisation.') % name
        Exception.__init__(self, message)

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

def get_settings_path(name):
    '''Get a directory to save user preferences.

    Different platforms have different conventions for where to save user
    preferences, saved games, and settings.  This function implements those
    conventions.  Note that the returned path may not exist: applications
    should use ``os.makedirs`` to construct it if desired.

    On Linux, a hidden directory `name` in the user's home directory is
    returned.

    On Windows (including under Cygwin) the `name` directory in the user's
    ``Application Settings`` directory is returned.

    On Mac OS X the `name` directory under ``~/Library/Application Support``
    is returned.

    :Parameters:
        `name` : str
            The name of the application.

    :rtype: str
    '''
    if sys.platform in ('cygwin', 'win32'):
        if 'APPDATA' in os.environ:
            return os.path.join(os.environ['APPDATA'], name)
        else:
            return os.path.expanduser('~/%s' % name)
    elif sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/%s' % name)
    else:
        return os.path.expanduser('~/.%s' % name)

class Loader(object):
    '''Load program resource files from disk.

    The loader contains a search path which can include filesystem
    directories, ZIP archives and Python packages.

    :Ivariables:
        `path` : list of str
            List of search locations.  After modifying the path you must
            call the `reindex` method.
        `script_home` : str
            Base resource location, defaulting to the location of the
            application script.

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

        '''
        if path is None:
            path = ['.', '@__main__']
        if type(path) in (str, unicode):
            path = [path]
        self.path = list(path)
        if script_home is None:
            script_home = get_script_home()
        self._script_home = script_home
        self.reindex()

        # Map name to image
        self._cached_textures = {}
        self._cached_images = {}

        # Map bin size to list of atlases
        self._texture_atlas_bins = {}

    def reindex(self):
        '''Refresh the file index.

        You must call this method if `path` is changed or the filesystem
        layout changes.
        '''
        self._index = {}
        for path in self.path:
            if path.startswith('@'):
                # Module
                name = path[1:]

                try:
                    module = __import__(name)
                except:
                    continue

                for component in name.split('.')[1:]:
                    module = getattr(module, component)

                if hasattr(module, '__file__'):
                    path = os.path.dirname(module.__file__)
                else:
                    path = '' # interactive
            elif not os.path.isabs(path):
                # Add script base unless absolute
                assert '\\' not in path, \
                    'Backslashes not permitted in relative path'
                path = os.path.join(self._script_home, path)

            if os.path.isdir(path):
                # Filesystem directory
                for name in os.listdir(path):
                    self._index_file(name, open, os.path.join(path, name))
            else:
                # Find path component that is the ZIP file.
                dir = ''
                while path and not os.path.isfile(path):
                    path, tail_dir = os.path.split(path)
                    dir = '/'.join((tail_dir, dir))
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

    def add_font(self, name):
        '''Add a font resource to the application.

        Fonts not installed on the system must be added to pyglet before they
        can be used with `font.load`.  Although the font is added with
        its filename using this function, it is loaded by specifying its
        family name.  For example::

            resource.add_font('action_man.ttf')
            action_man = font.load('Action Man')

        :Parameters:
            `name` : str
                Filename of the font resource to add.

        '''
        from pyglet import font
        file = self.file(name)
        font.add_file(file)

    def _alloc_image(self, name):
        file = self.file(name)
        img = pyglet.image.load(name, file=file)
        bin = self._get_texture_atlas_bin(img.width, img.height)
        if bin is None:
            return img.get_texture(True)

        return bin.add(img)

    def _get_texture_atlas_bin(self, width, height):
        '''A heuristic for determining the atlas bin to use for a given image
        size.  Returns None if the image should not be placed in an atlas (too
        big), otherwise the bin (a list of TextureAtlas).
        ''' 
        # Large images are not placed in an atlas
        if width > 128 or height > 128:
            return None

        # Group images with small height separately to larger height (as the
        # allocator can't stack within a single row).
        bin_size = 1
        if height > 32:
            bin_size = 2

        try:
            bin = self._texture_atlas_bins[bin_size]
        except KeyError:
            bin = self._texture_atlas_bins[bin_size] = \
                pyglet.image.atlas.TextureBin()

        return bin

    def image(self, name, flip_x=False, flip_y=False, rotate=0):
        '''Load an image with optional transformation.

        This is similar to `texture`, except the resulting image will be
        packed into a `TextureBin` if it is an appropriate size for packing.
        This is more efficient than loading images into separate textures.

        :Parameters:
            `name` : str
                Filename of the image source to load.
            `flip_x` : bool
                If True, the returned image will be flipped horizontally.
            `flip_y` : bool
                If True, the returned image will be flipped vertically.
            `rotate` : int
                The returned image will be rotated clockwise by the given
                number of degrees (a mulitple of 90).

        :rtype: `Texture`
        :return: A complete texture if the image is large, otherwise a
            `TextureRegion` of a texture atlas.
        '''
        if name in self._cached_images:
            identity = self._cached_images[name]
        else:
            identity = self._cached_images[name] = self._alloc_image(name)

        if not rotate and not flip_x and not flip_y:
            return identity
                
        return identity.get_transform(flip_x, flip_y, rotate)
       
    def get_cached_image_names(self):
        '''Get a list of image filenames that have been cached.

        This is useful for debugging and profiling only.

        :rtype: list
        :return: List of str
        '''
        return self._cached_images.keys()

    def get_texture_bins(self):
        '''Get a list of texture bins in use.

        This is useful for debugging and profiling only.

        :rtype: list
        :return: List of `TextureBin`
        '''
        return self._texture_atlas_bins.values()
       
    def media(self, name, streaming=True):
        '''Load a sound or video resource.

        The meaning of `streaming` is as for `media.load`.  Compressed
        sources cannot be streamed (that is, video and compressed audio
        cannot be streamed from a ZIP archive).

        :Parameters:
            `name` : str
                Filename of the media source to load.
            `streaming` : bool
                True if the source should be streamed from disk, False if
                it should be entirely decoded into memory immediately.

        :rtype: `media.Source`
        '''
        from pyglet import media
        try:
            func, path = self._index[name]
            if func is open:
                return media.load(path, streaming=streaming)
            else:
                return media.load(name, file=file, streaming=streaming)
        except KeyError:
            raise ResourceNotFoundException(name)

    def texture(self, name):
        '''Load a texture.

        The named image will be loaded as a single OpenGL texture.  If the
        dimensions of the image are not powers of 2 a `TextureRegion` will
        be returned.

        :Parameters:
            `name` : str
                Filename of the image resource to load.

        :rtype: `Texture`
        '''
        if name in self._cached_textures:
            return self._cached_textures[name]

        file = self.file(name)
        texture = pyglet.image.load(name, file=file).get_texture()
        self._cached_textures[name] = texture
        return texture

    def html(self, name):
        '''Load an HTML document.

        :Parameters:
            `name` : str
                Filename of the HTML resource to load.

        :rtype: `FormattedDocument`
        '''
        file = self.file(name)
        # TODO path!
        return pyglet.text.load(name, file, 'text/html')

    def attributed(self, name):
        '''Load an attributed text document.

        See `pyglet.text.formats.attributed` for details on this format.

        :Parameters:
            `name` : str
                Filename of the attribute text resource to load.

        :rtype: `FormattedDocument`
        '''
        file = self.file(name)
        return pyglet.text.load(name, file, 'text/vnd.pyglet-attributed')

    def text(self, name):
        '''Load a plain text document.

        :Parameters:
            `name` : str
                Filename of the plain text resource to load.

        :rtype: `UnformattedDocument`
        '''
        file = self.file(name)
        return pyglet.text.load(name, file, 'text/plain')

    def get_cached_texture_names(self):
        '''Get the names of textures currently cached.

        :rtype: list of str
        '''
        return self._cached_textures.keys()

#: Default resource search path.
#:
#: Locations in the search path are searched in order and are always
#: case-sensitive.  After changing the path you must call `reindex`.
#:
#: :type: list of str
path = []

class _DefaultLoader(Loader):
    def _get_path(self):
        return path

    def _set_path(self, value):
        global path
        path = value

    path = property(_get_path, _set_path)

_default_loader = _DefaultLoader()
reindex = _default_loader.reindex
file = _default_loader.file
add_font = _default_loader.add_font
image = _default_loader.image
get_cached_image_names = _default_loader.get_cached_image_names
get_texture_bins = _default_loader.get_texture_bins
media = _default_loader.media
texture = _default_loader.texture
html = _default_loader.html
attributed = _default_loader.attributed
text = _default_loader.text
get_cached_texture_names = _default_loader.get_cached_texture_names
