#!/usr/bin/env python
'''
'''

__docformat__ = 'restructuredtext'
__version__ = '1.2'

import sys
import textwrap

import pyglet
import pyglet.app
import pyglet.display
import pyglet.window
from pyglet.gl import *
from pyglet.gl import gl_info

print('Pyglet:     %s' % pyglet.version)
print('Platform:   %s' % sys.platform)
print('Event loop: %s' % pyglet.app.PlatformEventLoop.__name__)

display = pyglet.display.get_display()
print('Display:    %s' % display.__class__.__name__)
print('Screens:')
for screen in display.get_screens():
    print('  %r' % screen)

print()
print('Creating default context...')
w = pyglet.window.Window(1, 1, visible=True)
print('Window:')
print('  %s' % w)

print('GL attributes:')
attrs = w.config.get_gl_attributes()
attrs = ' '.join(['%s=%s'%(name, value) for name, value in attrs])
print(' ', '\n  '.join(textwrap.wrap(attrs)))

print('GL version:', gl_info.get_version())
print('GL vendor:', gl_info.get_vendor())
print('GL renderer:', gl_info.get_renderer())
print('GL extensions:')
exts = ' '.join(gl_info.get_extensions())
print(' ', '\n  '.join(textwrap.wrap(exts)))

print()

context = w.context
print('Context is', context)

if "xlib" in globals() and isinstance(context, xlib.BaseXlibContext):
    from pyglet.gl import glx_info
    print('GLX %s direct'%(context.is_direct() and 'is' or 'is not'))
    if not glx_info.have_version(1, 1):
        print("GLX server version: 1.0")
    else:
        print('GLX server vendor:', glx_info.get_server_vendor())
        print('GLX server version:', glx_info.get_server_version())
        print('GLX server extensions:')
        exts = glx_info.get_server_extensions()
        print(' ', '\n  '.join(textwrap.wrap(' '.join(exts))))
        print('GLX client vendor:', glx_info.get_client_vendor())
        print('GLX client version:', glx_info.get_client_version())
        print('GLX client extensions:')
        exts = glx_info.get_client_extensions()
        print(' ', '\n  '.join(textwrap.wrap(' '.join(exts))))
        print('GLX extensions:')
        exts = glx_info.get_extensions()
        print(' ', '\n  '.join(textwrap.wrap(' '.join(exts))))
elif "win32" in globals() and isinstance(context, win32.Win32Context):
    from pyglet.gl import wgl_info
    if wgl_info.have_extension('WGL_EXT_extensions_string'):
        wgl_extensions = wgl_info.get_extensions()
        print('WGL extensions:')
        print('', '\n '.join(textwrap.wrap(' '.join(wgl_extensions))))
    else:
        print('WGL_EXT_extensions_string extension not available.')

w.close()
