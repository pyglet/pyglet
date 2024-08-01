"""Load application resources from a known path.

Loading resources by specifying relative paths to filenames is often
problematic in Python, as the working directory is not necessarily the same
directory as the application's script files.

This module allows applications to specify a search path for resources.
Relative paths are taken to be relative to the application's ``__main__``
module. ZIP files can appear on the path; they will be searched inside.  The
resource module also behaves as expected when applications are bundled using
Freezers such as PyInstaller, Nuitka, py2app, etc..

In addition to providing file references (with the :py:func:`file` function),
the resource module also contains convenience functions for loading images,
textures, fonts, media and documents.

3rd party modules or packages not bound to a specific application should
construct their own :py:class:`Loader` instance and override the path to use the
resources in the module's directory.

Path format
^^^^^^^^^^^

The resource path :py:attr:`path` (see also :py:meth:`Loader.__init__` and
:py:meth:`Loader.path`)
is a list of locations to search for resources.  Locations are searched in the
order given in the path.  If a location is not valid (for example, if the
directory does not exist), it is skipped.

Locations in the path beginning with an "at" symbol (''@'') specify
Python packages.  Other locations specify a ZIP archive or directory on the
filesystem.  Locations that are not absolute are assumed to be relative to the
script home.  Some examples::

    # Search just the `res` directory, assumed to be located alongside the
    # main script file.
    path = ['res']

    # Search the directory containing the module `levels.level1`, followed
    # by the `res/images` directory.
    path = ['@levels.level1', 'res/images']

Paths are always **case-sensitive** and **forward slashes are always used**
as path separators, even in cases when the filesystem or platform does not do this.
This avoids a common programmer error when porting applications between platforms.

The default path is ``['.']``.  If you modify the path, you must call
:py:func:`reindex`.
"""
from __future__ import annotations

import os
import sys
import zipfile
import weakref

from io import BytesIO, StringIO
from typing import TYPE_CHECKING, IO

import pyglet

if TYPE_CHECKING:
    from typing import Literal
    from pyglet.graphics import Batch
    from pyglet.graphics.shader import Shader
    from pyglet.image import AbstractImage, Texture, TextureRegion
    from pyglet.image.animation import Animation
    from pyglet.image.atlas import TextureBin
    from pyglet.media.codecs import Source
    from pyglet.model import Model
    from pyglet.text.document import AbstractDocument


class ResourceNotFoundException(Exception):
    """The named resource was not found on the search path."""

    def __init__(self, name):
        message = (f"Resource '{name}' was not found on the path.  "
                   "Ensure that the filename has the correct capitalisation.")
        Exception.__init__(self, message)


class UndetectableShaderType(Exception):
    """The type of the Shader source could not be identified."""

    def __init__(self, name):
        message = (f"The Shader type of '{name}' could not be determined. "
                   "Ensure that your source file has a standard extension, "
                   "or provide a valid 'shader_type' parameter.")
        Exception.__init__(self, message)


def get_script_home() -> str:
    """Get the directory containing the program entry module.

    For ordinary Python scripts, this is the directory containing the
    ``__main__`` module. For applications that have been bundled with
    PyInstaller, Nuitka, etc., this may be the bundle path or a
    temporary directory.

    If none of the above cases apply and the file for ``__main__`` cannot
    be determined the working directory is returned.

    When the script is being run by a Python profiler, this function
    may return the directory where the profiler is running instead of
    the directory of the real script. To work around this behaviour the
    full path to the real script can be specified in :py:attr:`pyglet.resource.path`.
    """
    frozen = getattr(sys, 'frozen', None)
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        # PyInstaller
        return meipass
    elif frozen in ('windows_exe', 'console_exe'):
        return os.path.dirname(sys.executable)
    elif frozen == 'macosx_app':
        # py2app
        return os.environ['RESOURCEPATH']
    else:
        main = sys.modules['__main__']
        if hasattr(main, '__file__'):
            return os.path.dirname(os.path.abspath(main.__file__))
        else:
            if 'python' in os.path.basename(sys.executable):
                # interactive
                return os.getcwd()
            else:
                # cx_Freeze
                return os.path.dirname(sys.executable)


def get_settings_path(name: str) -> str:
    """Get a directory path to save user preferences.

    Different platforms have different conventions for where to save user
    preferences and settings. This function implements those conventions
    as described below, and returns a fully formed path.

    On Linux, a directory ``name`` in the user's configuration directory is
    returned (usually under ``~/.config``).

    On Windows (including under Cygwin) the ``name`` directory in the user's
    ``Application Settings`` directory is returned.

    On Mac OS X the ``name`` directory under ``~/Library/Application Support``
    is returned.

    .. note:: This function does not perform any directory creation. Users
              should use ``os.path.exists`` and ``os.makedirs`` to construct
              the directory if desired.
    """
    if pyglet.compat_platform in ('cygwin', 'win32'):
        if 'APPDATA' in os.environ:
            return os.path.join(os.environ['APPDATA'], name)
        else:
            return os.path.expanduser(f'~/{name}')
    elif pyglet.compat_platform == 'darwin':
        return os.path.expanduser(f'~/Library/Application Support/{name}')
    elif pyglet.compat_platform.startswith('linux'):
        if 'XDG_CONFIG_HOME' in os.environ:
            return os.path.join(os.environ['XDG_CONFIG_HOME'], name)
        else:
            return os.path.expanduser(f'~/.config/{name}')
    else:
        return os.path.expanduser(f'~/.{name}')


def get_data_path(name: str) -> str:
    """Get a directory to save user data.

    For a Posix or Linux based system many distributions have a separate
    directory to store user data for a specific application and this 
    function returns the path to that location.

    On Linux, a directory ``name`` in the user's data directory is returned
    (usually under ``~/.local/share``).

    On Windows (including under Cygwin) the ``name`` directory in the user's
    ``Application Settings`` directory is returned.

    On Mac OS X the ``name`` directory under ``~/Library/Application Support``
    is returned.

    .. note:: This function does not perform any directory creation. Users
              should use ``os.path.exists`` and ``os.makedirs`` to construct
              the directory if desired.
    """
    if pyglet.compat_platform in ('cygwin', 'win32'):
        if 'APPDATA' in os.environ:
            return os.path.join(os.environ['APPDATA'], name)
        else:
            return os.path.expanduser(f'~/{name}')
    elif pyglet.compat_platform == 'darwin':
        return os.path.expanduser(f'~/Library/Application Support/{name}')
    elif pyglet.compat_platform.startswith('linux'):
        if 'XDG_DATA_HOME' in os.environ:
            return os.path.join(os.environ['XDG_DATA_HOME'], name)
        else:
            return os.path.expanduser(f'~/.local/share/{name}')
    else:
        return os.path.expanduser(f'~/.{name}')


class Location:
    """Abstract resource location.

    Given a location, a file can be loaded from that location with the
    :py:meth:`open` method. This provides a convenient way to specify a
    path to load files from, even when that path does not reside on the
    filesystem.
    """

    def open(self, name: str, mode: str = 'rb') -> BytesIO | StringIO | IO:
        """Open a file at this location.

        Args:
            name:
                The file name to open. Absolute paths are not supported.
                Relative paths are not supported by most locations (you
                should specify only a file name with no path component).
            mode:
                The file mode to open with.  Only files opened on the
                filesystem make use of this parameter; others ignore it.
        """
        raise NotImplementedError('abstract')


class FileLocation(Location):
    """Location on the filesystem."""

    def __init__(self, filepath: str) -> None:
        """Create a location given a relative or absolute path."""
        self.path = filepath

    def open(self, filename: str, mode: str = 'rb') -> IO:
        return open(os.path.join(self.path, filename), mode)


class ZIPLocation(Location):
    """Location within a ZIP file."""

    def __init__(self, zipfileobj: zipfile.ZipFile, directory: str | None):
        """Create a location given an open ZIP file and a path within that
        file.

        Args:
            zipfileobj:
                An open ZIP file from the ``zipfile`` module.
            directory:
                A path within that ZIP file.  Can be empty to specify files at
                the top level of the ZIP file.
        """
        self.zip = zipfileobj
        self.dir = directory

    def open(self, filename: str, mode='rb') -> BytesIO | StringIO:
        """Open a file from inside the ZipFile.

        Args:
            filename:
                The filename to open.
            mode:
                Valid modes are 'r' and 'rb'.
        """
        _path = f"{self.dir}/{filename}" if self.dir else filename
        _forward_slash_path = _path.replace(os.sep, '/')  # zip can only handle forward slashes
        _bytes = self.zip.read(_forward_slash_path)
        if mode == 'r':
            return StringIO(_bytes.decode())
        return BytesIO(_bytes)


class URLLocation(Location):
    """Location on the network.

    This class uses the ``urllib`` module to open files on
    the network, given a base URL.
    """

    def __init__(self, base_url: str) -> None:
        """Create a location given a base URL."""
        self.base = base_url

    def open(self, filename: str, mode: str = '') -> IO:
        """Open a remote file.

        Args:
            filename:
                The name of the remote resource to open.
            mode:
                Unused, as the mode is determined by the remote server.
        """
        import urllib.parse
        import urllib.request
        url = urllib.parse.urljoin(self.base, filename)
        return BytesIO(urllib.request.urlopen(url).read())


class Loader:
    """Load program resource files from disk.

    The loader contains a search path which can include filesystem
    directories, ZIP archives, URLs, and Python packages.
    """
    def __init__(self, pathlist: list[str] | None = None, script_home: str | None = None) -> None:
        """Create a loader for the given path.

        If no path is specified it defaults to ``['.']``; that is,
        just the program directory.

        See the module documentation for details on the path format.

        Args:
            pathlist:
                List of locations to search for resources.
            script_home:
                Base location of relative files. Defaults to
                the result of :py:func:`get_script_home`.
        """
        pathlist = pathlist or ['.']

        if isinstance(pathlist, str):
            pathlist = [pathlist]

        self.path = list(pathlist)
        self._script_home = script_home or get_script_home()
        self._index: dict | None = None

        # Map bin size to list of atlases
        self._texture_atlas_bins = {}

        # map name to image etc.
        self._cached_textures = weakref.WeakValueDictionary()
        self._cached_images = weakref.WeakValueDictionary()
        self._cached_animations = weakref.WeakValueDictionary()

    def _ensure_index(self):
        if self._index is None:
            self.reindex()

    def _index_file(self, name: str, locationobj: Location) -> None:
        if name not in self._index:
            self._index[name] = locationobj

    def reindex(self):
        """Refresh the file index.

        You must call this method if ``resource.path`` is changed,
        or the filesystem layout changes.
        """
        self._index = {}
        for _path_name in self.path:

            # A Python module:
            if _path_name.startswith('@'):
                module_name = _path_name[1:]
                try:
                    module = __import__(module_name)
                except (ImportError, ValueError):
                    continue
                for component in module_name.split('.')[1:]:
                    module = getattr(module, component)
                if hasattr(module, '__file__'):
                    _path_name = os.path.dirname(module.__file__)
                else:
                    _path_name = ''  # interactive

            elif not os.path.isabs(_path_name):
                # Add script base unless absolute
                assert r'\\' not in _path_name, "Backslashes are not permitted in relative paths"
                _path_name = os.path.join(self._script_home, _path_name)

            # A filesystem directory:
            if os.path.isdir(_path_name):
                _path_name = _path_name.rstrip(os.path.sep)
                file_location = FileLocation(_path_name)
                for dirpath, dirnames, filenames in os.walk(_path_name):
                    dirpath = dirpath[len(_path_name) + 1:]
                    # Force forward slashes for index
                    if dirpath:
                        parts = [part for part in dirpath.split(os.sep) if part is not None]
                        dirpath = '/'.join(parts)
                    for filename in filenames:
                        if dirpath:
                            index_name = dirpath + '/' + filename
                        else:
                            index_name = filename
                        self._index_file(index_name, file_location)

            else:
                # Find path component that looks like the ZIP file.
                zip_directory = ''
                old_path = None
                while _path_name and not (os.path.isfile(_path_name) or os.path.isfile(_path_name + '.001')):
                    old_path = _path_name
                    _path_name, tail_dir = os.path.split(_path_name)
                    if _path_name == old_path:
                        break
                    zip_directory = '/'.join((tail_dir, zip_directory))
                if _path_name == old_path:
                    continue
                zip_directory = zip_directory.rstrip('/')

                # path looks like a ZIP file, zip_directory resides within ZIP
                if not _path_name:
                    continue

                if zip_stream := self._get_stream(_path_name):
                    zipfileobj = zipfile.ZipFile(zip_stream, 'r')
                    file_location = ZIPLocation(zipfileobj, zip_directory)
                    for zip_name in zipfileobj.namelist():
                        # zip_name_dir, zip_name = os.path.split(zip_name)
                        # assert '\\' not in name_dir
                        # assert not name_dir.endswith('/')
                        if zip_name.startswith(zip_directory):
                            if zip_directory:
                                zip_name = zip_name[len(zip_directory) + 1:]
                            self._index_file(zip_name, file_location)

    @staticmethod
    def _get_stream(pathname: str) -> IO | str | None:
        if zipfile.is_zipfile(pathname):
            return pathname
        elif not os.path.exists(pathname + '.001'):
            return None
        else:
            with open(pathname + '.001', 'rb') as volume:
                bytes_ = bytes(volume.read())

            volume_index = 2
            while os.path.exists(pathname + '.{0:0>3}'.format(volume_index)):
                with open(pathname + '.{0:0>3}'.format(volume_index), 'rb') as volume:
                    bytes_ += bytes(volume.read())

                volume_index += 1

            zip_stream = BytesIO(bytes_)
            if zipfile.is_zipfile(zip_stream):
                return zip_stream
            else:
                return None

    def file(self, name: str, mode: str = 'rb') -> BytesIO | StringIO | IO:
        """Load a file-like object.

        Args:
            name:
                Filename of the resource to load.
            mode:
                Combination of ``r``, ``w``, ``a``, ``b`` and ``t`` characters
                with the meaning as for the builtin ``open`` function.
        """
        self._ensure_index()
        try:
            file_location = self._index[name]
            return file_location.open(name, mode)
        except KeyError:
            raise ResourceNotFoundException(name)

    def location(self, filename: str) -> FileLocation | URLLocation | ZIPLocation:
        """Get the location of a resource.

        This method is useful for opening files referenced from a resource.
        For example, an HTML file loaded as a resource might reference some
        images.  These images should be located relative to the HTML file, not
        looked up individually in the loader's path.
        """
        self._ensure_index()
        try:
            return self._index[filename]
        except KeyError:
            raise ResourceNotFoundException(filename)

    def add_font(self, filename: str) -> None:
        """Add a font resource to the application.

        Fonts not installed on the system must be added to pyglet before they
        can be used with ``font.load``. Although the font is added with its
        filename using this function, fonts are always loaded by specifying
        their family name. For example::

            resource.add_font('action_man.ttf')
            action_man = font.load('Action Man')

        """
        self._ensure_index()
        from pyglet import font
        fileobj = self.file(filename)
        font.add_file(fileobj)

    def _alloc_image(self, name: str, use_atlas: bool, border: int) -> AbstractImage:
        fileobj = self.file(name)
        try:
            img = pyglet.image.load(name, file=fileobj)
        finally:
            fileobj.close()

        if not use_atlas:
            return img.get_texture()

        # Add the image to a TextureAtlasBin, if possible
        if texture_bin := self._get_texture_atlas_bin(img.width, img.height, border):
            return texture_bin.add(img, border)

        return img.get_texture()

    def _get_texture_atlas_bin(self, width: int, height: int, border: int) -> TextureBin | None:
        """A heuristic for determining the atlas bin to use for a given image
        size.  Returns None if the image should not be placed in an atlas (too
        big), otherwise the bin (a list of TextureAtlas).
        """
        # Large images are not placed in an atlas
        max_texture_size = pyglet.image.get_max_texture_size()
        max_size = min(2048, max_texture_size) - border
        if width > max_size or height > max_size:
            return None

        # Group images with small height separately to larger height
        # (as the allocator can't stack within a single row).
        bin_size = 1
        if height > max_size / 4:
            bin_size = 2

        try:
            texture_bin = self._texture_atlas_bins[bin_size]
        except KeyError:
            texture_bin = pyglet.image.atlas.TextureBin()
            self._texture_atlas_bins[bin_size] = texture_bin

        return texture_bin

    def image(self, name: str, flip_x: bool = False, flip_y: bool = False, rotate: Literal[0, 90, 180, 270, 360] = 0,
              atlas: bool = True, border: int = 1) -> Texture | TextureRegion:
        """Load an image with optional transformation.

        This is similar to `texture`, except the resulting image will be
        packed into a :py:class:`~pyglet.image.atlas.TextureBin` (TextureAtlas)
        if it is an appropriate size for packing. This is more efficient than
        loading images into separate textures.

        Args:
            name:
                The filename of the image source to load.
            flip_x:
                If ``True``, the returned image will be flipped horizontally.
            flip_y:
                If ``True``, the returned image will be flipped vertically.
            rotate:
                The returned image will be rotated clockwise by the given
                number of degrees (a multiple of 90).
            atlas:
                If ``True``, the image will be loaded into an atlas managed by
                pyglet. If atlas loading is not appropriate for specific texturing
                reasons (e.g. border control is required) then set to ``False``.
            border:
                Leaves specified pixels of blank space around each image in
                an atlas, which may help reduce texture bleeding.

        .. note:: When using ``flip_x/y`` or ``rotate``, the actual image
                  data is not modified. Instead, the texture coordinates
                  are manipulated to produce the desired result.
        """
        self._ensure_index()
        if name in self._cached_images:
            identity = self._cached_images[name]
        else:
            identity = self._cached_images[name] = self._alloc_image(name, atlas, border)

        if not rotate and not flip_x and not flip_y:
            return identity

        return identity.get_transform(flip_x, flip_y, rotate)

    def animation(self, name: str, flip_x: bool = False, flip_y: bool = False,
                  rotate: Literal[0, 90, 180, 270, 360] = 0, border: int = 1) -> Animation:
        """Load an animation with optional transformation.

        Animations loaded from the same source but with different
        transformations will use the same textures.

        Args:
            name:
                Filename of the animation source to load.
            flip_x:
                If ``True``, the returned image will be flipped horizontally.
            flip_y:
                If ``True``, the returned image will be flipped vertically.
            rotate:
                The returned image will be rotated clockwise by the given
                number of degrees (must be a multiple of 90).
            border:
                Leaves specified pixels of blank space around each image in
                an atlas, which may help reduce texture bleeding.
        """
        self._ensure_index()
        try:
            identity = self._cached_animations[name]
        except KeyError:
            _animation = pyglet.image.load_animation(name, self.file(name))
            texture_bin = self._get_texture_atlas_bin(_animation.get_max_width(),
                                                      _animation.get_max_height(),
                                                      border)
            if texture_bin:
                _animation.add_to_texture_bin(texture_bin, border)

            identity = self._cached_animations[name] = _animation

        if not rotate and not flip_x and not flip_y:
            return identity

        return identity.get_transform(flip_x, flip_y, rotate)

    def get_cached_animation_names(self) -> list[str]:
        """Get a list of animation filenames that have been cached.

        This is useful for debugging and profiling only.
        """
        self._ensure_index()
        return list(self._cached_animations.keys())

    def get_cached_image_names(self) -> list[str]:
        """Get a list of image filenames that have been cached.

        This is useful for debugging and profiling only.
        """
        self._ensure_index()
        return list(self._cached_images.keys())

    def get_cached_texture_names(self) -> list[str]:
        """Get a list of texture filenames that have been cached.

        This is useful for debugging and profiling only.
        """
        self._ensure_index()
        return list(self._cached_textures.keys())

    def get_texture_bins(self) -> list[TextureBin]:
        """Get a list of texture bins in use.

        This is useful for debugging and profiling only.
        """
        self._ensure_index()
        return list(self._texture_atlas_bins.values())

    def media(self, name: str, streaming: bool = True) -> Source:
        """Load a sound or video resource.

        The meaning of ``streaming`` is as for :py:func:`~pyglet.media.load`.
        Compressed sources cannot be streamed (that is, video and compressed
        audio cannot be streamed from a ZIP archive).

        Args:
            name:
                Filename of the media source to load.
            streaming:
                True if the source should be streamed from disk, False if
                it should be entirely decoded into memory immediately.
        """
        self._ensure_index()
        from pyglet import media
        try:
            file_location = self._index[name]
            if isinstance(location, FileLocation):
                # Don't open the file if it's streamed from disk
                file_path = os.path.join(file_location.path, name)
                return media.load(file_path, streaming=streaming)
            else:
                fileobj = file_location.open(name)

                return media.load(name, file=fileobj, streaming=streaming)
        except KeyError:
            raise ResourceNotFoundException(name)

    def texture(self, name: str) -> Texture:
        """Load an image as a single OpenGL texture."""
        self._ensure_index()
        if name in self._cached_textures:
            return self._cached_textures[name]

        fileobj = self.file(name)
        textureobj = pyglet.image.load(name, file=fileobj).get_texture()
        self._cached_textures[name] = textureobj
        return textureobj

    def model(self, name: str, batch: Batch | None = None) -> Model:
        """Load a 3D model.

        Args:
            name:
                Filename of the 3D model to load.
            batch:
                An optional Batch instance to add this model to.
        """
        self._ensure_index()
        abspathname = os.path.join(os.path.abspath(self.location(name).path), name)
        return pyglet.model.load(filename=abspathname, file=self.file(name), batch=batch)

    def html(self, name: str) -> AbstractDocument:
        """Load an HTML document."""
        self._ensure_index()
        fileobj = self.file(name)
        return pyglet.text.load(name, fileobj, 'text/html')

    def attributed(self, name: str) -> AbstractDocument:
        """Load an attributed text document.

        See `pyglet.text.formats.attributed` for details on this format.
        """
        self._ensure_index()
        fileobj = self.file(name)
        return pyglet.text.load(name, fileobj, 'text/vnd.pyglet-attributed')

    def text(self, name: str) -> AbstractDocument:
        """Load a plain text document."""
        self._ensure_index()
        fileobj = self.file(name)
        return pyglet.text.load(name, fileobj, 'text/plain')

    def shader(self, name: str, shader_type: str | None = None) -> Shader:
        """Load a Shader object.

        Args:
            name:
                Filename of the Shader source to load.
            shader_type:
                A hint for the type of shader, such as 'vertex', 'fragment', etc.
                Not required if your shader has a standard file extension, such
                as ``.vert``, ``.frag``, etc..
        """
        self._ensure_index()
        # https://www.khronos.org/opengles/sdk/tools/Reference-Compiler/
        shader_extensions = {'comp': "compute",
                             'frag': "fragment",
                             'geom': "geometry",
                             'tesc': "tescontrol",
                             'tese': "tesevaluation",
                             'vert': "vertex"}
        fileobj = self.file(name, 'r')
        source_string = fileobj.read()

        if not shader_type:
            try:
                _, extension = os.path.splitext(name)
                shader_type = shader_extensions[extension.strip(".")]
            except KeyError:
                raise UndetectableShaderType(name=name)

        if shader_type not in shader_extensions.values():
            raise UndetectableShaderType(name=name)

        return pyglet.graphics.shader.Shader(source_string, shader_type)


#: Default resource search path.
#:
#: Locations in the search path are searched in order and are always
#: case-sensitive.  After changing the path you must call `reindex`.
#:
#: See the module documentation for details on the path format.
#:
#: :type: list of str
path = []


class _DefaultLoader(Loader):

    @property
    def path(self):
        return path

    @path.setter
    def path(self, value):
        global path
        path = value


_default_loader = _DefaultLoader()
reindex = _default_loader.reindex
file = _default_loader.file
location = _default_loader.location
add_font = _default_loader.add_font
image = _default_loader.image
animation = _default_loader.animation
model = _default_loader.model
media = _default_loader.media
texture = _default_loader.texture
html = _default_loader.html
attributed = _default_loader.attributed
text = _default_loader.text
shader = _default_loader.shader
get_cached_texture_names = _default_loader.get_cached_texture_names
get_cached_image_names = _default_loader.get_cached_image_names
get_cached_animation_names = _default_loader.get_cached_animation_names
get_texture_bins = _default_loader.get_texture_bins
