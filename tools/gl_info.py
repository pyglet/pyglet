#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import textwrap

import pyglet.window
from pyglet.gl import *
from pyglet.gl import gl_info
from pyglet.gl import glu_info

platform = pyglet.window.get_platform()
print 'Platform instance is %r' % platform
display = platform.get_default_display()
print 'Display instance is %r' % display
print 'Screens:'
for screen in display.get_screens():
    print '  %r' % screen

print 'Creating default context...'
w = pyglet.window.Window(1, 1, visible=True)

print 'GL attributes:'
attrs = w.config.get_gl_attributes()
attrs = ' '.join(['%s=%s'%(name, value) for name, value in attrs])
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

context = w.context
print 'Context is', context

if context.__class__.__name__ == 'XlibGLContext':
    from pyglet.gl import glx_info
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
    from pyglet.gl import wgl_info
    if wgl_info.have_extension('WGL_EXT_extensions_string'):
        wgl_extensions = wgl_info.get_extensions()
        print 'WGL extensions:'
        print '', '\n '.join(textwrap.wrap(' '.join(wgl_extensions)))
    else:
        print 'WGL_EXT_extensions_string extension not available.'

w.close()
