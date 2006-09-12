#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
import os
import re
import sys
import textwrap

dependencies = {
    'GL_VERSION_2_0': ('pyglet.GL.VERSION_1_5',),
    'GL_VERSION_1_5': ('pyglet.GL.VERSION_1_4',),
    'GL_VERSION_1_4': ('pyglet.GL.VERSION_1_3',),
    'GL_VERSION_1_3': ('pyglet.GL.VERSION_1_2',),
    'GL_VERSION_1_2': ('pyglet.GL.VERSION_1_1',),

    'GLX_VERSION_1_4': ('pyglet.window.xlib.glx.VERSION_1_3',),
    'GLX_VERSION_1_3': ('pyglet.window.xlib.glx.VERSION_1_2',),
    'GLX_VERSION_1_2': ('pyglet.window.xlib.glx.VERSION_1_1',),
}

basic_types = {
    'char': '_ctypes.c_char',
    'int': '_ctypes.c_int',
    'long': '_ctypes.c_long',
    'unsigned': '_ctypes.c_uint',
    'void': 'None',
    'ptrdiff_t': '_c_ptrdiff_t',

    # From /usr/include/GL/gl.h
    'GLenum': '_ctypes.c_uint',
    'GLboolean': '_ctypes.c_ubyte',
    'GLbitfield': '_ctypes.c_uint',
    'GLbyte': '_ctypes.c_byte',
    'GLshort': '_ctypes.c_short',
    'GLint': '_ctypes.c_int',
    'GLsizei': '_ctypes.c_int',
    'GLubyte': '_ctypes.c_ubyte',
    'GLushort': '_ctypes.c_ushort',
    'GLuint': '_ctypes.c_uint',
    'GLfloat': '_ctypes.c_float',
    'GLclampf': '_ctypes.c_float',
    'GLdouble': '_ctypes.c_double',
    'GLclampd': '_ctypes.c_double',
    'GLvoid': 'None',

    # From /usr/include/X11/X.h
    'XID': '_ctypes.c_ulong',
    'Window': '_ctypes.c_ulong',
    'Drawable': '_ctypes.c_ulong',
    'Pixmap': '_ctypes.c_ulong',
    'Bool': '_ctypes.c_int',

    # From /System/Library/Frameworks/AGL.framework/Headers/agl.h
    'AGLDevice': '_ctypes.c_void_p',
    'AGLDrawable': '_ctypes.c_void_p',
    'AGLRendererInfo': '_ctypes.c_void_p',
    'AGLPixelFormat': '_ctypes.c_void_p',
    'AGLContext': '_ctypes.c_void_p',
    'AGLPBuffer': '_ctypes.c_void_p',

    # From MacTypes.h
    'Style': '_ctypes.c_ubyte',
}

basic_tokens = {
    # Avoid VERSION_2_0 dependency on ARB_imaging
    'GL_BLEND_EQUATION': '0x8009',
}

def replace_token(out, groups):
    value = basic_tokens.get(groups[1], groups[1])
    out.write('%s = %s\n' % (groups[0], value))

def replace_type(out, groups):
    ctype = basic_types.get(groups[0], groups[0])
    if ctype.split()[0] not in ('struct', 'union'):
        out.write('%s = %s\n' % (groups[1], ctype))

def type_to_ctype(t):
    ctype = ''
    pieces = t.split()
    pointers = 0
    for piece in pieces:
        pointers += piece.count('*')
        piece = piece.strip('* ')
        if piece == 'const':
            continue
        if not ctype:
            ctype = basic_types.get(piece, piece)
    for i in range(pointers):
        if ctype == 'None':
            ctype = '_ctypes.c_void_p'
        elif ctype in ('_ctypes.c_char', '_ctypes.c_ubyte'):
            ctype = '_ctypes.c_char_p'
        else:
            ctype = '_ctypes.POINTER(%s)' % ctype
    return ctype

def replace_function(out, groups):
    ctype_args = []
    rtype, name, args = groups
    
    rtype = type_to_ctype(rtype)
    for arg in args.split(','):
        ctype_args.append(type_to_ctype(arg))
    if ctype_args == ['None']:
        ctype_args = []
    out.write('%s = _get_function(%r, [%s], %s)\n' % \
                (name, name, ', '.join(ctype_args), rtype))

replacements = [
    # token for GLEW
    (re.compile('^([A-Z][A-Z0-9_]*)\s+((?:0x)?[0-9A-F]+|[A-Z][A-Z0-9_]*)$'),
     replace_token),    
    # token for gl.h
    (re.compile('^#define\s+([A-Z][A-Z0-9_]*)\s+((?:0x)?[0-9A-F]+|[A-Z][A-Z0-9_]*)\s*/\*.*$'),
     replace_token),
    # typedef
    (re.compile('^typedef\s+(.+)\s+([\*A-Za-z0-9_]+)$'),
     replace_type),
    # gl.h function prototype
    (re.compile('^WINGDIAPI\s+(.+)\s+APIENTRY\s+([a-zA-Z][a-zA-Z0-9_]*)\s+\((.+)\);$'),
     replace_function),
    # glx.h function prototype (requires lines to be unwrapped first)
    (re.compile('^extern\s+(.+)\s+([a-zA-Z][a-zA-Z0-9_]*)\((.+)\);$'),
     replace_function),
    # agl.h function prototype
    (re.compile('^extern\s+(.+)\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\((.+)\).*;$'),
     replace_function),
    # GLEW function prototype
    (re.compile('^(.+) ([a-zA-Z][a-zA-Z0-9_]*) \((.+)\)$'),
     replace_function),
]

def gl2ctypes(gl_filename, py_filename, glew=False):
    gl = open(gl_filename, 'r')
    if glew:
        name, url = gl.readline().strip(), gl.readline().strip()
        prefix, name = name.split('_', 1)
    else:
        name = 'VERSION_1_1'
        url = gl_filename
    lines = gl.readlines()

    if url[:7] != 'http://':
        # Not really the URL
        lines.insert(0, url)
        url = ''

    out = open(py_filename, 'w')
    out.write(textwrap.dedent('''
        """%s
        %s
        """

        import ctypes as _ctypes
        from pyglet.GL import get_function as _get_function
        from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
        ''' % (name, url)))
    fullname = os.path.splitext(os.path.basename(gl_filename))[0]
    for dependency in dependencies.get(fullname, []):
        out.write('from %s import *\n' % dependency)
    # Must do patterns in correct order, (typedefs before functions)
    for pattern, func in replacements:
        for line in lines:
            line = line.strip()
            match = pattern.match(line)
            if match:
                func(out, match.groups())

def usage():
    print textwrap.dedent('''
    gl2ctypes.py something.h something.py

        Convert something.h to something.py

    gl2ctypes.py /usr/lib/GL/gl.h pyglet/GL/

        Convert gl.h to pyglet/GL/VERSION_1_1.py

    gl2ctypes.py --glew     glew/auto/ pyglet/GL/ [extension ...]
    gl2ctypes.py --glew-glx glew/auto/ pyglet/window/xlib/glx/ [extension ...]

        First argument is location of GLEW auto directory (containing
        "core" and "extensions" subdirectories).  Second argument
        is output directory for Python files.  Optionally specify
        which extensions to convert, otherwise it will convert all
        the extensions it finds.
        ''')
    sys.exit(1)

def main(args):
    del args[0]

    if len(args) < 2:
        usage()

    if args[0] == '--glew':
        del args[0]
        main_glew(args, 'GL')
    elif args[0] == '--glew-glx':
        del args[0]
        main_glew(args, 'GLX')
    elif os.path.isdir(args[1]):
        gl2ctypes(args[0], os.path.join(args[1], 'VERSION_1_1.py'))
    else:
        gl2ctypes(args[0], args[1])


def main_glew(args, file_prefix):
    auto_dir = args[0]
    output_dir = args[1]
    extensions = args[2:]
    for dir in ('core', 'extensions'):
        dir = os.path.join(auto_dir, dir)
        for file in os.listdir(dir):
            if '_' in file:
                prefix, name = file.split('_', 1)
                if name[0].isdigit():
                    name = '_' + name
                if prefix == file_prefix and \
                   (not extensions or name in extensions):
                    gl2ctypes(os.path.join(dir, file), 
                              os.path.join(output_dir, '%s.py' % name), True)

if __name__ == '__main__':
    main(sys.argv)
