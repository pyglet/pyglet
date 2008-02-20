#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import operator
import os
import sys
import zipfile
import StringIO

import rectallocator

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

    def preload_font(self, name):
        '''Add a font resource to the application.

        Fonts not installed on the system must be preloaded before they
        can be used with `font.load`.  Although the font is preloaded with
        its filename using this function, it is loaded by specifying its
        family name.  For example::

            resource.preload_font('action_man.ttf')
            action_man = font.load('Action Man')

        :Parameters:
            `name` : str
                Filename of the font resource to preload.

        '''
        from pyglet import font
        file = self.file(name)
        font.add_file(file)

    def preload_fonts(self, *names):
        if names:
            for name in names:
                self.preload_font(name)
        else:
            raise NotImplementedError('TODO')

    def preload_fonts_iter(self, *names):
        raise NotImplementedError('TODO')

    def _alloc_image(self, name, pad):
        # XXX pad is ignored (probably not needed?)
        from pyglet import image
        file = self.file(name)
        img = image.load(name, file=file)
        bin = self._get_texture_atlas_bin(img.width, img.height)
        if bin is None:
            return img.get_texture(True)

        # Try atlases until image fits
        for atlas in bin:
            try:
                return atlas.add(img)
            except rectallocator.AllocatorException:
                pass

        # No atlases could accept image, create a new one (all atlases are
        # 256x256, an arbitrary choice).
        atlas = TextureAtlas(256, 256)
        bin.append(atlas)
        return atlas.add(img)

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

        if bin_size in self._texture_atlas_bins:
            bin = self._texture_atlas_bins[bin_size]
        else:
            bin = self._texture_atlas_bins[bin_size] = []

        return bin

    def image(self, name, pad=0, flip_x=False, flip_y=False, rotate=0):
        '''
        '''
        if name in self._cached_images:
            identity = self._cached_images[name]
        else:
            identity = self._cached_images[name] = self._alloc_image(name, pad)

        if not rotate and not flip_x and not flip_y:
            return identity
                
        return identity.get_transform(flip_x, flip_y, rotate)
        
    def preload_images(self, *names):
        raise NotImplementedError('TODO')

    def preload_images_iter(self, *names):
        raise NotImplementedError('TODO')

    def get_cached_image_names(self):
        return self._cached_images.keys()

    def get_texture_atlases(self):
        return reduce(operator.add, self._texture_atlas_bins.values())

    def get_texture_atlas_usage(self):
        usage = 0.0
        count = 0
        for bin in self._texture_atlas_bins:
            for atlas in bin:
                usage += atlas.allocator.get_usage()
                count += 1
        return usage / count

    def get_texture_atlas_fragmentation(self):
        fragmentation = 0.0
        count = 0
        for bin in self._texture_atlas_bins:
            for atlas in bin:
                usage += atlas.allocator.get_fragmentation()
                count += 1
        return fragmentation / count 
        
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
        from pyglet import image
        if name in self._cached_textures:
            return self._cached_textures[name]

        file = self.file(name)
        texture = image.load(name, file=file).get_texture()
        self._cached_textures[name] = texture
        return texture

    def get_cached_texture_names(self):
        '''Get the names of textures currently cached.

        :rtype: list of str
        '''
        return self._cached_textures.keys()

class TextureAtlas(object):
    def __init__(self, width, height):
        from pyglet import gl
        from pyglet import image
        self.texture = image.Texture.create_for_size(
            gl.GL_TEXTURE_2D, width, height, internalformat=gl.GL_RGBA)
        self.allocator = rectallocator.RectAllocator(width, height)

    def add(self, img):
        x, y = self.allocator.alloc(img.width, img.height)
        self.texture.blit_into(img, x, y, 0)
        return self.texture.get_region(x, y, img.width, img.height)

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
preload_font = _default_loader.preload_font
preload_fonts = _default_loader.preload_fonts
preload_fonts_iter = _default_loader.preload_fonts_iter
image = _default_loader.image
preload_images = _default_loader.preload_images
preload_images_iter = _default_loader.preload_images_iter
get_cached_image_names = _default_loader.get_cached_image_names
get_texture_atlases = _default_loader.get_texture_atlases
get_texture_atlas_usage = _default_loader.get_texture_atlas_usage
get_texture_atlas_fragmentation = \
    _default_loader.get_texture_atlas_fragmentation
media = _default_loader.media
texture = _default_loader.texture
get_cached_texture_names = _default_loader.get_cached_texture_names
