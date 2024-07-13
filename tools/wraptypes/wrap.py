"""Generate a Python ctypes wrapper file for a header file.

Usage example::
    wrap.py -lGL -oGL.py /usr/include/GL/gl.h

    >>> from GL import *

"""
from __future__ import annotations

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import textwrap

from ctypesparser import *


class CtypesWrapper(CtypesParser, CtypesTypeVisitor):
    file=None
    def begin_output(self, output_file, library, link_modules=(), 
                     emit_filenames=(), all_headers=False):
        self.library = library
        self.file = output_file
        self.all_names = []
        self.known_types = {}
        self.structs = set()
        self.enums = set()
        self.emit_filenames = emit_filenames
        self.all_headers = all_headers

        self.linked_symbols = {}
        for name in link_modules:
            module = __import__(name, globals(), locals(), ['foo'])
            for symbol in dir(module):
                if symbol not in self.linked_symbols:
                    self.linked_symbols[symbol] = '%s.%s' % (name, symbol)
        self.link_modules = link_modules

        self.print_preamble()
        self.print_link_modules_imports()

    def wrap(self, filename, source=None):
        assert self.file, 'Call begin_output first'
        self.parse(filename, source)

    def end_output(self):
        self.print_epilogue()
        self.file = None

    def does_emit(self, symbol, filename):
        return self.all_headers or filename in self.emit_filenames

    def print_preamble(self):
        import textwrap
        print(textwrap.dedent("""
            '''Wrapper for {library}

            Generated with:
            {argv}

            Do not modify this file.
            '''

            __docformat__ =  'restructuredtext'
            __version__ = '$Id$'

            import ctypes
            from ctypes import *

            import pyglet.lib

            _lib = pyglet.lib.load_library({library!r})

            _int_types = (c_int16, c_int32)
            if hasattr(ctypes, 'c_int64'):
                # Some builds of ctypes apparently do not have c_int64
                # defined; it's a pretty good bet that these builds do not
                # have 64-bit pointers.
                _int_types += (ctypes.c_int64,)
            for t in _int_types:
                if sizeof(t) == sizeof(c_size_t):
                    c_ptrdiff_t = t

            class c_void(Structure):
                # c_void_p is a buggy return type, converting to int, so
                # POINTER(None) == c_void_p is actually written as
                # POINTER(c_void), so it can be treated as a real pointer.
                _fields_ = [('dummy', c_int)]

        """.format(
            library=self.library,
            argv=' '.join(sys.argv),
        )).lstrip(), file=self.file)

    def print_link_modules_imports(self) -> None:
        for name in self.link_modules:
            print(f'import {name}', file=self.file)
        print(file=self.file)

    def print_epilogue(self) -> None:
        print(file=self.file)
        print('\n'.join(textwrap.wrap(
            '__all__ = [{}]'.format(', '.join([repr(n) for n in self.all_names])),
            width=78,
            break_long_words=False)), file=self.file)

    def handle_ctypes_constant(self, name, value, filename, lineno) -> None:
        if self.does_emit(name, filename):
            print(f'{name} = {value!r}', end=' ', file=self.file)
            print('\t# %s:%d' % (filename, lineno), file=self.file)
            self.all_names.append(name)

    def handle_ctypes_type_definition(self, name, ctype, filename, lineno) -> None:
        if self.does_emit(name, filename):
            self.all_names.append(name)
            if name in self.linked_symbols:
                print(f'{name} = {self.linked_symbols[name]}', file=self.file)
            else:
                ctype.visit(self)
                self.emit_type(ctype)
                print(f'{name} = {ctype!s}', end=' ', file=self.file)
                print('\t# %s:%d' % (filename, lineno), file=self.file)
        else:
            self.known_types[name] = (ctype, filename, lineno)

    def emit_type(self, t) -> None:
        t.visit(self)
        for s in t.get_required_type_names():
            if s in self.known_types:
                if s in self.linked_symbols:
                    print(f'{s} = {self.linked_symbols[s]}', file=self.file)
                else:
                    s_ctype, s_filename, s_lineno = self.known_types[s]
                    s_ctype.visit(self)

                    self.emit_type(s_ctype)
                    print(f'{s} = {s_ctype!s}', end=' ', file=self.file)
                    print('\t# %s:%d' % (s_filename, s_lineno), file=self.file)
                del self.known_types[s]

    def visit_struct(self, struct) -> None:
        if struct.tag in self.structs:
            return
        self.structs.add(struct.tag)

        base = {True: 'Union', False: 'Structure'}[struct.is_union]
        print(f'class struct_{struct.tag}({base}):', file=self.file)
        print('    __slots__ = [', file=self.file)
        if not struct.opaque:
            for m in struct.members:
                print(f"        '{m[0]}',", file=self.file)
        print('    ]', file=self.file)

        # Set fields after completing class, so incomplete structs can be
        # referenced within struct.
        for _name, typ in struct.members:
            self.emit_type(typ)

        print(f'struct_{struct.tag}._fields_ = [', file=self.file)
        if struct.opaque:
            print("    ('_opaque_struct', c_int)", file=self.file)
            self.structs.remove(struct.tag)
        else:
            for m in struct.members:
                print(f"    ('{m[0]}', {m[1]}),", file=self.file)
        print(']', file=self.file)
        print(file=self.file)

    def visit_enum(self, enum) -> None:
        if enum.tag in self.enums:
            return
        self.enums.add(enum.tag)

        print(f'enum_{enum.tag} = c_int', file=self.file)
        for name, value in enum.enumerators:
            self.all_names.append(name)
            print('%s = %d' % (name, value), file=self.file)

    def handle_ctypes_function(self, name, restype, argtypes, filename, lineno) -> None:
        if self.does_emit(name, filename):
            # Also emit any types this func requires that haven't yet been
            # written.
            self.emit_type(restype)
            for a in argtypes:
                self.emit_type(a)

            self.all_names.append(name)
            print('# %s:%d' % (filename, lineno), file=self.file)
            print(f'{name} = _lib.{name}', file=self.file)
            print(f'{name}.restype = {restype!s}', file=self.file)
            print('{}.argtypes = [{}]'.format(name, ', '.join([str(a) for a in argtypes])), file=self.file)
            print(file=self.file)

    def handle_ctypes_variable(self, name, ctype, filename, lineno) -> None:
        # This doesn't work.  (but I(shenjackyuanjie) still remove the '%' content
        # self.all_names.append(name)
        # print >> self.file, f'{name} = {str(ctype)}.indll(_lib, {name!r})'
        pass

def main(*argv) -> None:
    import optparse
    import os.path
    import sys

    usage = 'usage: %prog [options] <header.h>'
    op = optparse.OptionParser(usage=usage)
    op.add_option('-o', '--output', dest='output',
                  help='write wrapper to FILE', metavar='FILE')
    op.add_option('-l', '--library', dest='library',
                  help='link to LIBRARY', metavar='LIBRARY')
    op.add_option('-D', '--define', dest='defines', default=[],
                  help='define token NAME=VALUE', action='append')
    op.add_option('-i', '--include-file', action='append', dest='include_files',
                  help='assume FILE is iincluded', metavar='FILE',
                  default=[])
    op.add_option('-I', '--include-dir', action='append', dest='include_dirs',
                  help='add DIR to include search path', metavar='DIR',
                  default=[])
    op.add_option('-m', '--link-module', action='append', dest='link_modules',
                  help='use symbols from MODULE', metavar='MODULE',
                  default=[])
    op.add_option('-a', '--all-headers', action='store_true',
                  dest='all_headers',
                  help='include symbols from all headers', default=False)

    (options, args) = op.parse_args(list(argv[1:]))
    if len(args) < 1:
        print('No header files specified.', file=sys.stderr) 
        sys.exit(1)
    headers = args

    if options.library is None:
        options.library = os.path.splitext(headers[0])[0]
    if options.output is None:
        options.output = f'{options.library}.py'

    wrapper = CtypesWrapper()
    wrapper.begin_output(open(options.output, 'w'),
                         library=options.library,
                         emit_filenames=headers,
                         link_modules=options.link_modules,
                         all_headers=options.all_headers)
    wrapper.preprocessor_parser.include_path += options.include_dirs
    for define in options.defines:
        name, value = define.split('=')
        wrapper.preprocessor_parser.define(name, value)
    for file in options.include_files:
        wrapper.wrap(file)
    for header in headers:
        wrapper.wrap(header)
    wrapper.end_output()

    print(f'Wrapped to {options.output}')

if __name__ == '__main__':
    main(*sys.argv)
