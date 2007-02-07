#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from wraptypes.wrap import main as wrap
import os.path
import sys

if __name__ == '__main__':
    if not os.path.exists('pyglet/window'):
        assert False, 'Run with CWD = trunk root.'
    if sys.platform == 'linux2':
        wrap('tools/wraptypes/wrap.py',
             '-opyglet/window/xlib/xlib.py',
             '-lX11',
             '-mpyglet.GL.glx',
             '/usr/include/X11/Xlib.h',
             '/usr/include/X11/Xutil.h')
        wrap('tools/wraptypes/wrap.py',
             '-opyglet/window/xlib/xinerama.py',
             '-lXinerama',
             '-mpyglet.GL.glx',
             '-mpyglet.window.xlib.xlib',
             '/usr/include/X11/extensions/Xinerama.h')
