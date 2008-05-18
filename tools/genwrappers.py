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
        if 'pulseaudio' in names:
            wrap('tools/wraptypes/wrap.py',
                 '-oexperimental/pulse/lib_pulseaudio.py',
                 '-lpulse',
                 '-i/usr/include/pulse/pulseaudio.h',
                 '/usr/include/pulse/mainloop-api.h',
                 '/usr/include/pulse/sample.h',
                 '/usr/include/pulse/def.h',
                 '/usr/include/pulse/context.h',
                 '/usr/include/pulse/stream.h',
                 '/usr/include/pulse/introspect.h',
                 '/usr/include/pulse/subscribe.h',
                 '/usr/include/pulse/scache.h',
                 '/usr/include/pulse/version.h',
                 '/usr/include/pulse/error.h',
                 '/usr/include/pulse/operation.h',
                 '/usr/include/pulse/channelmap.h',
                 '/usr/include/pulse/volume.h',
                 '/usr/include/pulse/xmalloc.h',
                 '/usr/include/pulse/utf8.h',
                 '/usr/include/pulse/thread-mainloop.h',
                 '/usr/include/pulse/mainloop.h',
                 '/usr/include/pulse/mainloop-signal.h',
                 '/usr/include/pulse/util.h',
                 '/usr/include/pulse/timeval.h')
