#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import fcntl
import time
import struct
import sys

import pyglet
import pyglet.window

display = pyglet.window.get_platform().get_default_display()
w = pyglet.window.Window(display=display)
@w.event
def on_draw():
    w.clear()

# assume off_t is 64-bits
lock = struct.pack('HHQQI', fcntl.F_WRLCK, 0, 0, 1, 0)
tmpfile = os.tmpfile()
fcntl.fcntl(tmpfile, fcntl.F_SETLK, lock)

if os.fork() == 0:
    # Child polls until parent has released lock (by dying).
    time.sleep(1)
    while True:
        try:
            fcntl.fcntl(tmpfile, fcntl.F_SETLK, lock)
            break
        except IOError:
            time.sleep(1)
    print 'child activated'
else:
    # Parent runs indefinitely (until window is closed)
    pyglet.app.run()
    print 'parent finished.'
