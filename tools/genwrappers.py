#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from wraptypes.wrap import main as wrap
import os.path
import sys

import pyglet
pyglet.options['shadow_window'] = False

if __name__ == '__main__':
    if not os.path.exists('pyglet/window'):
        assert False, 'Run with CWD = trunk root.'
    names = sys.argv[1:]
    if sys.platform == 'linux2':
        if 'xlib' in names:    
            wrap('tools/wraptypes/wrap.py',
                 '-opyglet/window/xlib/xlib.py',
                 '-lX11',
                 '-mpyglet.gl.glx',
                 '/usr/include/X11/Xlib.h',
                 '/usr/include/X11/X.h',
                 '/usr/include/X11/Xutil.h')
        if 'xinerama' in names:
            wrap('tools/wraptypes/wrap.py',
                 '-opyglet/window/xlib/xinerama.py',
                 '-lXinerama',
                 '-mpyglet.gl.glx',
                 '-mpyglet.window.xlib.xlib',
                 '/usr/include/X11/extensions/Xinerama.h')
        if 'xsync' in names:
            print '------------------------------------'
            print 'WARNING xsync requires import hacks.'
            print ' ... copy over from current xsync.py'
            print '------------------------------------'
            wrap('tools/wraptypes/wrap.py',
                 '-opyglet/window/xlib/xsync.py',
                 '-lXext',
                 '-mpyglet.window.xlib.xlib',
                 '-i/usr/include/X11/Xlib.h',
                 '-i/usr/include/X11/X.h',
                 '-i/usr/include/X11/Xdefs.h',
                 '-DStatus=int',
                 '/usr/include/X11/extensions/sync.h')
        if 'xinput' in names:
            wrap('tools/wraptypes/wrap.py',
                 '-oexperimental/input/lib_xinput.py',
                 '-lXi',
                 '-mpyglet.window.xlib.xlib',
                 '-i/usr/include/X11/Xlib.h',
                 '-i/usr/include/X11/X.h',
                 '-i/usr/include/X11/Xdefs.h',
                 '/usr/include/X11/extensions/XInput.h',
                 '/usr/include/X11/extensions/XI.h')
        if 'xrandr' in names:
            wrap('tools/wraptypes/wrap.py',
                 '-oexperimental/modeswitch/lib_xrandr.py',
                 '-lXrandr',
                 '-mpyglet.window.xlib.xlib',
                 '-i/usr/include/X11/Xlib.h',
                 '-i/usr/include/X11/X.h',
                 '-i/usr/include/X11/Xdefs.h',
                 '/usr/include/X11/extensions/Xrandr.h',
                 '/usr/include/X11/extensions/randr.h')
