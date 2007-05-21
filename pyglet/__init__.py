#!/usr/bin/env python

'''pyglet is a cross-platform games and multimedia package.

Detailed documentation is available at http://www.pyglet.org
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

def _require_ctypes_version(version):
    # Check ctypes version
    import ctypes
    req = [int(i) for i in version.split('.')]
    have = [int(i) for i in ctypes.__version__.split('.')]
    if not tuple(have) >= tuple(req):
        raise ImportError('pyglet requires ctypes %s or later.' % version)
_require_ctypes_version('1.0.0')

#: Global dict of pyglet options.  To change an option from its default, you
#: must import `pyglet` before any sub-packages.  For example::
#:
#:      import pyglet
#:      pyglet.options['gl_error_check'] = False
#:
#: The options are:
#:
#: gl_error_check
#:     If True, all calls to OpenGL functions are checked afterwards for
#:     errors using ``glGetError``.  This will severely impact performance,
#:     but provides useful exceptions at the point of failure.  By default,
#:     this option is enabled if ``__debug__`` is (i.e., if Python was not run
#:     with the -O option.
#:
options = {
    'gl_error_check': __debug__,
}
