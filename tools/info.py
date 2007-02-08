#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import textwrap

import pyglet.window
from pyglet.gl import *
from pyglet.gl.gl_info import *
from pyglet.gl.glu_info import *

platform = pyglet.window.get_platform()
print 'Platform instance is %r' % platform
factory = pyglet.window.get_factory()
print 'Screens:'
for screen in factory.get_screens():
    print '  %r' % screen

print 'Creating default context...'
w = pyglet.window.Window(1, 1, visible=False)

print 'GL attributes:'
order = ['buffer_size', 'doublebuffer', 'stereo', 'red_size', 'green_size',
    'blue_size', 'alpha_size', 'aux_buffers', 'depth_size', 'stencil_size',
    'accum_red_size', 'accum_green_size', 'accum_blue_size',
    'accum_alpha_size']
attrs = w.get_config().get_gl_attributes()
attrs = ' '.join(['%s=%s'%(i, attrs[i]) for i in order])
print '\n'.join(textwrap.wrap(attrs))

print 'GL version:', gl_info.get_version()
print 'GL vendor:', gl_info.get_vendor()
print 'GL renderer:', gl_info.get_renderer()
print 'GL extensions:'
exts = ' '.join(gl_info.get_extensions())
print ' ', '\n  '.join(textwrap.wrap(exts))

print 'GLU version:', glu_info.get_version()
print 'GLU extensions:'
exts = ' '.join(glu_info.get_extensions())
print ' ', '\n  '.join(textwrap.wrap(exts))

print

context = w.get_context()
print 'Context is', context

if context.__class__.__name__ == 'XlibGLContext':
    from pyglet.gl.glx_info import *
    print 'GLX %s direct'%(context.is_direct() and 'is' or 'is not')
    if not glx_info.have_version(1, 1):
        print "GLX server version: 1.0"
    else:
        print 'GLX server vendor:', glx_info.get_server_vendor()
        print 'GLX server version:', glx_info.get_server_version()
        print 'GLX server extensions:'
        exts = glx_info.get_server_extensions()
        print ' ', '\n  '.join(textwrap.wrap(' '.join(exts)))
        print 'GLX client vendor:', glx_info.get_client_vendor()
        print 'GLX client version:', glx_info.get_client_version()
        print 'GLX client extensions:'
        exts = glx_info.get_client_extensions()
        print ' ', '\n  '.join(textwrap.wrap(' '.join(exts)))
        print 'GLX extensions:'
        exts = glx_info.get_extensions()
        print ' ', '\n  '.join(textwrap.wrap(' '.join(exts)))
elif context.__class__.__name__ == 'Win32Context':
    from pyglet.gl.wgl_info import have_wgl_extension, get_wgl_extensions
    if have_wgl_extension('WGL_EXT_extensions_string'):
        wgl_extensions = get_wgl_extensions()
        print 'WGL extensions:'
        print '', '\n '.join(textwrap.wrap(' '.join(wgl_extensions)))
    else:
        print 'WGL_EXT_extensions_string extension not available.'

