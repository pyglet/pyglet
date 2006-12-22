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
    d = w._display
    print 'GLX %s direct'%(context.is_direct() and 'is' or 'is not')
    from pyglet.window.xlib import have_glx_version
    if not have_glx_version(d, 1, 1):
        print "GLX server version: 1.0"
        print "(and can't be bothered to enquire about anything else)"
    else:
        from pyglet.window.xlib.glx.VERSION_1_3 import *
        print 'GLX server vendor:', glXQueryServerString(w._display, 0,
            GLX_VENDOR)
        print 'GLX server version:', glXQueryServerString(w._display, 0,
            GLX_VERSION)
        print 'GLX server extensions:'
        exts = glXQueryServerString(w._display, 0, GLX_EXTENSIONS)
        print ' ', '\n  '.join(textwrap.wrap(exts))
        print 'GLX client vendor:', glXGetClientString(w._display,
            GLX_VENDOR)
        print 'GLX client version:', glXGetClientString(w._display,
            GLX_VERSION)
        print 'GLX client extensions:'
        exts = glXGetClientString(w._display, GLX_EXTENSIONS)
        print ' ', '\n  '.join(textwrap.wrap(exts))
        print 'GLX extensions:'
        exts = glXQueryExtensionsString(w._display, 0)
        print ' ', '\n '.join(textwrap.wrap(exts))

