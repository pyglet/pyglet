#!/usr/bin/env python

'''Functions for loading dynamic libraries.

These extend and correct ctypes functions.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import os
import sys

import ctypes
import ctypes.util

class LibraryLoader(object):
    def load_library(self, *names, **kwargs):
        '''Find and load a library.  
        
        More than one name can be specified, they will be tried in order.
        Platform-specific library names (given as kwargs) are tried first.

        Raises ImportError if library is not found.
        '''
        platform_names = kwargs.get(self.platform, [])
        if type(platform_names) in (str, unicode):
            platform_names = (platform_names,)
        elif type(platform_names) == list:
            platform_names = tuple(list)
        for name in platform_names + names:
            path = self.find_library(name)
            if path:
                return ctypes.cdll.LoadLibrary(path)
        raise ImportError('Library "%s" not found.' % names[0])

    find_library = ctypes.util.find_library

    platform = sys.platform
    if platform == 'cygwin':
        platform = 'win32'

class MachOLibraryLoader(LibraryLoader):
    def __init__(self):
        if 'LD_LIBRARY_PATH' in os.environ:
            self.ld_library_path = os.environ['LD_LIBRARY_PATH'].split(':')
        else:
            self.ld_library_path = []

        if 'DYLD_LIBRARY_PATH' in os.environ:
            self.dyld_library_path = os.environ['DYLD_LIBRARY_PATH'].split(':')
        else:
            self.dyld_library_path = []

        if 'DYLD_FALLBACK_LIBRARY_PATH' in os.environ:
            self.dyld_fallback_library_path = \
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'].split(':')
        else:
            self.dyld_fallback_library_path = [
                os.path.expanduser('~/lib'),
                '/usr/local/lib',
                '/usr/lib']
 
    def find_library(self, path):
        '''Implements the dylib search as specified in Apple documentation:
        
        http://developer.apple.com/documentation/DeveloperTools/Conceptual/DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html
        '''

        libname = os.path.basename(path)
        if '/' in path:
            search_path = (
                [os.path.join(p, libname) \
                    for p in self.dyld_library_path] +
                [path] + 
                [os.path.join(p, libname) \
                    for p in self.dyld_fallback_library_path])
        else:
            search_path = (
                [os.path.join(p, libname) \
                    for p in self.ld_library_path] +
                [os.path.join(p, libname) \
                    for p in self.dyld_library_path] +
                [path] + 
                [os.path.join(p, libname) \
                    for p in self.dyld_fallback_library_path])

        for path in search_path:
            if os.path.exists(path):
                return path

        return None


if sys.platform == 'darwin':
    loader = MachOLibraryLoader()
else:
    loader = LibraryLoader()
load_library = loader.load_library
