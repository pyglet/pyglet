"""Functions for loading dynamic libraries.

These extend and correct ctypes functions.
"""
from __future__ import annotations

import os
import re
import sys
import contextlib

import ctypes
import ctypes.util

import pyglet
from typing import NoReturn, Callable, Any

_debug_lib = pyglet.options['debug_lib']
_debug_trace = pyglet.options['debug_trace']

_is_pyglet_doc_run = getattr(sys, "is_pyglet_doc_run", False)

if pyglet.options['search_local_libs']:
    script_path = pyglet.resource.get_script_home()
    cwd = os.getcwd()
    _local_lib_paths = [script_path, os.path.join(script_path, 'lib'), os.path.join(cwd, 'lib')]
    if pyglet.compat_platform == 'win32':
        os.environ["PATH"] += os.pathsep + os.pathsep.join(_local_lib_paths)
else:
    _local_lib_paths = None


class _TraceFunction:
    def __init__(self, func: Callable) -> None:
        self.__dict__['_func'] = func

    def __str__(self) -> str:
        return self._func.__name__

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._func, name)

    def __setattr__(self, name: str, value: object) -> None:
        setattr(self._func, name, value)


class _TraceLibrary:
    def __init__(self, library: Any) -> None:
        self._library = library
        print(library)

    def __getattr__(self, name: str) -> Callable:
        func = getattr(self._library, name)
        return _TraceFunction(func)


if _is_pyglet_doc_run:
    class LibraryMock:
        """Mock library used when generating documentation."""
        def __getattr__(self, name: str):
            return LibraryMock()

        def __setattr__(self, name: str, value) -> None:
            pass

        def __call__(self, *args, **kwargs):
            return LibraryMock()

        def __rshift__(self, other: LibraryMock):
            return 0


class LibraryLoader:  # noqa: D101

    platform = pyglet.compat_platform
    # this is only for library loading, don't include it in pyglet.platform
    if platform == 'cygwin':
        platform = 'win32'

    def load_library(self, *names: str, **kwargs):
        """Find and load a library.

        More than one name can be specified, they will be tried in order.
        Platform-specific library names (given as kwargs) are tried first.

        Raises ImportError if library is not found.
        """
        if _is_pyglet_doc_run:
            return LibraryMock()

        if 'framework' in kwargs and self.platform == 'darwin':
            return self.load_framework(kwargs['framework'])

        if not names:
            msg = "No library name specified"
            raise ImportError(msg)

        platform_names = kwargs.get(self.platform, [])
        if isinstance(platform_names, str):
            platform_names = [platform_names]
        elif type(platform_names) is tuple:
            platform_names = list(platform_names)

        if self.platform.startswith('linux'):
            for name in names:
                libname = self.find_library(name)
                platform_names.append(libname or f'lib{name}.so')

        platform_names.extend(names)
        for name in platform_names:
            try:
                lib = ctypes.cdll.LoadLibrary(name)
                if _debug_lib:
                    print(name, self.find_library(name))
                if _debug_trace:
                    lib = _TraceLibrary(lib)
                return lib
            except OSError as o: # noqa: PERF203
                path = self.find_library(name)
                if path:
                    try:
                        lib = ctypes.cdll.LoadLibrary(path)
                        if _debug_lib:
                            print(path)
                        if _debug_trace:
                            lib = _TraceLibrary(lib)
                        return lib
                    except OSError as e:
                        if _debug_lib:
                            print(f"Unexpected error loading library {name}: {e!s}")
                elif self.platform == "win32" and o.winerror != 126 and _debug_lib:
                    print(f"Unexpected error loading library {name}: {o!s}")

        msg = f'Library "{names[0]}" not found.'
        raise ImportError(msg)

    def find_library(self, name: str) -> str | None:
        return ctypes.util.find_library(name)

    @staticmethod
    def load_framework(_name: str) -> NoReturn:
        msg = "Can't load framework on this platform."
        raise RuntimeError(msg)


class MacOSLibraryLoader(LibraryLoader):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        if 'LD_LIBRARY_PATH' in os.environ:
            self.ld_library_path = os.environ['LD_LIBRARY_PATH'].split(':')
        else:
            self.ld_library_path = []

        if _local_lib_paths:
            # search first for local libs
            self.ld_library_path = _local_lib_paths + self.ld_library_path
            os.environ['LD_LIBRARY_PATH'] = ':'.join(self.ld_library_path)

        if 'DYLD_LIBRARY_PATH' in os.environ:
            self.dyld_library_path = os.environ['DYLD_LIBRARY_PATH'].split(':')
        else:
            self.dyld_library_path = []

        if 'DYLD_FALLBACK_LIBRARY_PATH' in os.environ:
            self.dyld_fallback_library_path = os.environ['DYLD_FALLBACK_LIBRARY_PATH'].split(':')
        else:
            self.dyld_fallback_library_path = [os.path.expanduser('~/lib'), '/usr/local/lib', '/usr/lib']

            # Homebrew path on Apple Silicon is no longer in local.
            if 'HOMEBREW_PREFIX' in os.environ:
                # if HOMEBREW_PREFIX is defined, add its lib directory.
                brew_lib_path = os.path.join(os.environ['HOMEBREW_PREFIX'], 'lib')
                if os.path.exists(brew_lib_path):
                    self.dyld_fallback_library_path.append(brew_lib_path)
            else:
                # Check the typical path if the environmental variable is missing.
                if os.path.exists('/opt/homebrew/lib'):
                    self.dyld_fallback_library_path.append('/opt/homebrew/lib')


    def find_library(self, path: str) -> str | None:
        """Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/library/content/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        """  # noqa: D415
        libname = os.path.basename(path)
        search_path = []

        if '.dylib' not in libname:
            libname = 'lib' + libname + '.dylib'

        # py2app support
        if getattr(sys, 'frozen', None) == 'macosx_app' and 'RESOURCEPATH' in os.environ:
            search_path.append(os.path.join(os.environ['RESOURCEPATH'],
                                            '..',
                                            'Frameworks',
                                            libname))

        # conda support
        if os.environ.get('CONDA_PREFIX', False):
            search_path.append(os.path.join(os.environ['CONDA_PREFIX'], 'lib', libname))

        # pyinstaller.py sets sys.frozen to True, and puts dylibs in
        # Contents/macOS, which path pyinstaller puts in sys._MEIPASS
        if getattr(sys, 'frozen', False) and (meipass := getattr(sys, '_MEIPASS', None)):
            search_path.append(os.path.join(meipass, libname))

        # conda support
        if os.environ.get('CONDA_PREFIX', False):
            search_path.append(os.path.join(os.environ['CONDA_PREFIX'], 'lib', libname))

        if '/' in path:
            search_path.extend([os.path.join(p, libname) for p in self.dyld_library_path])
            search_path.append(path)
            search_path.extend([os.path.join(p, libname) for p in self.dyld_fallback_library_path])
        else:
            search_path.extend([os.path.join(p, libname) for p in self.ld_library_path])
            search_path.extend([os.path.join(p, libname) for p in self.dyld_library_path])
            search_path.append(path)
            search_path.extend([os.path.join(p, libname) for p in self.dyld_fallback_library_path])

        for path in search_path:
            if os.path.exists(path):
                return path

        return None

    @staticmethod
    def load_framework(name: str) -> ctypes.CDLL | _TraceLibrary:
        path = ctypes.util.find_library(name)

        # Hack for compatibility with macOS > 11.0  # noqa: FIX004
        if path is None:
            frameworks = {
                'AGL': '/System/Library/Frameworks/AGL.framework/AGL',
                'IOKit': '/System/Library/Frameworks/IOKit.framework/IOKit',
                'OpenAL': '/System/Library/Frameworks/OpenAL.framework/OpenAL',
                'OpenGL': '/System/Library/Frameworks/OpenGL.framework/OpenGL',
            }
            path = frameworks.get(name)

        if path:
            lib = ctypes.cdll.LoadLibrary(path)
            if _debug_lib:
                print(path)
            if _debug_trace:
                lib = _TraceLibrary(lib)
            return lib

        msg = f"Can't find framework {name}."
        raise ImportError(msg)


class LinuxLibraryLoader(LibraryLoader):  # noqa: D101
    _ld_so_cache = None
    _local_libs_cache = None

    @staticmethod
    def _find_libs(directories: list[str]) -> dict[str, str]:
        libs = {}
        lib_re = re.compile(r'lib(.*)\.so(?:$|\.)')
        for directory in directories:
            try:
                for file in os.listdir(directory):
                    match = lib_re.match(file)
                    if match:
                        # Index by filename
                        path = os.path.join(directory, file)
                        if file not in libs:
                            libs[file] = path
                        # Index by library name
                        library = match.group(1)
                        if library not in libs:
                            libs[library] = path
            except OSError:  # noqa: PERF203
                pass
        return libs

    def _create_ld_so_cache(self) -> None:
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = []
        with contextlib.suppress(KeyError):
            directories.extend(os.environ['LD_LIBRARY_PATH'].split(':'))

        with contextlib.suppress(OSError), open('/etc/ld.so.conf') as fid:
            directories.extend([directory.strip() for directory in fid])

        directories.extend(['/lib', '/usr/lib'])

        self._ld_so_cache = self._find_libs(directories)

    def find_library(self, path: str) -> str:

        # search first for local libs
        if _local_lib_paths:
            if not self._local_libs_cache:
                self._local_libs_cache = self._find_libs(_local_lib_paths)
            if path in self._local_libs_cache:
                return self._local_libs_cache[path]

        # ctypes tries ldconfig, gcc and objdump.  If none of these are
        # present, we implement the ld-linux.so search path as described in
        # the man page.

        result = ctypes.util.find_library(path)

        if result:
            return result

        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        return self._ld_so_cache.get(path)


if pyglet.compat_platform == 'darwin':
    loader = MacOSLibraryLoader()
elif pyglet.compat_platform.startswith('linux'):
    loader = LinuxLibraryLoader()
else:
    loader = LibraryLoader()

load_library = loader.load_library
