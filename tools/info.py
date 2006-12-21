#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import textwrap

import pyglet.window
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
import pyglet.GL.info
import pyglet.GLU.info

w = pyglet.window.Window(1, 1, visible=False)

print 'GL attributes:'
order = ['buffer_size', 'doublebuffer', 'stereo', 'red_size', 'green_size',
    'blue_size', 'alpha_size', 'aux_buffers', 'depth_size', 'stencil_size',
    'accum_red_size', 'accum_green_size', 'accum_blue_size',
    'accum_alpha_size']
attrs = w.get_config().get_gl_attributes()
attrs = ' '.join(['%s=%s'%(i, attrs[i]) for i in order])
print '\n'.join(textwrap.wrap(attrs))

print 'GL version:', pyglet.GL.info.get_version()
print 'GL vendor:', pyglet.GL.info.get_vendor()
print 'GL renderer:', pyglet.GL.info.get_renderer()
print 'GL extensions:'
exts = ' '.join(pyglet.GL.info.get_extensions())
print ' ', '\n  '.join(textwrap.wrap(exts))

print 'GLU version:', pyglet.GLU.info.get_version()
print 'GLU extensions:'
exts = ' '.join(pyglet.GLU.info.get_extensions())
print ' ', '\n  '.join(textwrap.wrap(exts))

print

context = w.get_context()
print 'Context is', context

if context.__class__.__name__ == 'XlibGLContext':
    print 'GLX %s direct'%(context.is_direct() and 'is' or 'is not')
    print 'GLX server vendor:', context.get_server_vendor()
    print 'GLX server version:', context.get_server_version()
    print 'GLX server extensions:'
    exts = ' '.join(context.get_server_extensions())
    print ' ', '\n  '.join(textwrap.wrap(exts))
    print 'GLX client vendor:', context.get_client_vendor()
    print 'GLX client version:', context.get_client_version()
    print 'GLX client extensions:'
    exts = ' '.join(context.get_client_extensions())
    print ' ', '\n  '.join(textwrap.wrap(exts))
    print 'GLX extensions:'
    exts = ' '.join(context.get_extensions())
    print ' ', '\n  '.join(textwrap.wrap(exts))

