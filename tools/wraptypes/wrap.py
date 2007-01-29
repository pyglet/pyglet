#!/usr/bin/env python

'''Generate a Python ctypes wrapper file for a header file.

Usage example::
    wrap.py -lGL -oGL.py /usr/include/GL/gl.h

    >>> from GL import *

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypesparser import *

class CtypesWrapper(CtypesParser):
    def __init__(self, library, file):
        super(CtypesWrapper, self).__init__()
        self.library = library
        self.file = file
        self.all_names = []

    def wrap(self, filename, source=None):
        self.print_preamble()
        self.parse(filename, source)
        self.print_epilogue()

    def print_preamble(self):
        import textwrap
        import time
        print >> self.file, textwrap.dedent("""
            '''Wrapper for %(library)s
            
            Generated %(date)s by %(class)s.  
            Do not modify this file.
            '''

            __docformat__ =  'restructuredtext'
            __version__ = '$Id$'

            from ctypes import *
            from ctypes.util import find_library as _find_library

            _libpath = _find_library(%(library)r)
            if not _libpath:
                raise ImportError('Could not locate %(library)s library')
            _lib = cdll.LoadLibrary(_libpath)
        """ % {
            'library': self.library,
            'date': time.ctime(),
            'class': self.__class__.__name__,
        }).lstrip()

    def print_epilogue(self):
        print >> self.file, '__all__ = [%s]' % \
            ','.join([repr(n) for n in self.all_names])

    def handle_ctypes_constant(self, name, value):
        self.all_names.append(name)
        print >> self.file, '%s = %r' % (name, value)

    def handle_ctypes_type_definition(self, name, ctype):
        self.all_names.append(name)
        print >> self.file, '%s = %s' % (name, str(ctype))

    def handle_ctypes_function(self, name, restype, argtypes):
        self.all_names.append(name)
        print >> self.file, '%s = _lib.%s' % (name, name)
        print >> self.file, '%s.restype = %s' % (name, str(restype))
        print >> self.file, '%s.argtypes = [%s]' % \
            (name, ', '.join([str(a) for a in argtypes])) 

    def handle_ctypes_variable(self, name, ctype):
        self.all_names.append(name)
        print >> self.file, '%s = %s.indll(_lib, %r)' % \
            (name, str(ctype), name)

if __name__ == '__main__':
    import optparse
    import sys
    import os.path

    usage = 'usage: %prog [options] <header.h>'
    op = optparse.OptionParser(usage=usage)
    op.add_option('-o', '--output', dest='output',
                  help='write wrapper to FILE', metavar='FILE')
    op.add_option('-l', '--library', dest='library',
                  help='link to LIBRARY', metavar='LIBRARY')
    
    (options, args) = op.parse_args()
    if len(args) < 1:
        print >> sys.stderr, 'No header file specified.'
        sys.exit(1)
    header = args[0]

    if options.library is None:
        options.library = os.path.splitext(header)[0]
    if options.output is None:
        options.output = '%s.py' % options.library

    wrapper = CtypesWrapper(options.library, open(options.output, 'w'))
    wrapper.wrap(header)

    print 'Wrapped to %s' % options.output
