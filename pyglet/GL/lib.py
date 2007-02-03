#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import ctypes

__all__ = ['link_GL', 'link_GLU']

class MissingFunctionException(Exception):
    def __init__(self, name, requires=None, suggestions=None):
        msg = '%s is not exported by the available OpenGL driver.' % name
        if requires:
            msg += '  %s is required for this functionality.' % requires
        if suggestions:
            msg += '  Consider alternative(s) %s.' % ', '.join(suggestions)
        Exception.__init__(self, msg)

def missing_function(name, requires=None, suggestions=None):
    def MissingFunction(*args, **kwargs):
        raise MissingFunctionException(name, requires, suggestions)
    return MissingFunction

_int_types = (ctypes.c_int16, ctypes.c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (ctypes.c_int64,)
for t in _int_types:
    if ctypes.sizeof(t) == ctypes.sizeof(ctypes.c_size_t):
        c_ptrdiff_t = t

if sys.platform in ('win32', 'cygwin'):
    from pyglet.GL.lib_wgl import link_GL, link_GLU
elif sys.platform == 'darwin':
    from pyglet.GL.lib_agl import link_GL, link_GLU
else:
    from pyglet.GL.lib_glx import link_GL, link_GLU

