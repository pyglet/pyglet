#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys

__all__ = ['link_function']

class MissingFunctionException(Exception):
    def __init__(self, name, requires=None, suggestions=None):
        msg = '%s is not exported by the available OpenGL driver.'
        if requires:
            msg += '  %s is required for this functionality.'
        if suggestions:
            msg += '  Consider alternative(s) %s.' % ', '.join(suggestions)
        super(MissingFunctionException, self).__init__(msg)

def missing_function(name, requires=None, suggestions=None):
    def MissingFunction(*args, **kwargs):
        raise MissingFunctionException(name, requires, suggestions)
    return MissingFunction
            
if sys.platform in ('win32', 'cygwin'):
    from pyglet.GL.lib_wgl import link_function
elif sys.platform == 'darwin':
    from pyglet.GL.lib_agl import link_function
else:
    from pyglet.GL.lib_glx import link_function

